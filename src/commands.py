import dataclasses
import datetime
import jinja2
import logging
import pprint
import pathlib
import typing
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import db_datamodel
from db_datamodel import (
    Base,
    Category,
    Keyword,
    DB_NAME,
    Episode,
    Episode_2_episode
)
import rss_datamodel
from rss_datamodel import (
    analyse_channel_data,
    download_current_feed,
    poor_mans_csv_parser,
    read_feed
)
import episode_links

LOGGER = logging.getLogger('command')

THIS_FILE_FOLDER = pathlib.Path(__file__).parent.resolve()

ORGANIC_NAME_SEPARATOR = '|'

def _delete_db():
    try:
        pathlib.Path.unlink(DB_NAME.resolve())
    except:
        print('Nothing to delete')


def _split_organic_category(c: str) -> typing.Tuple[str, str]:
    """analyze first char to determine category"""
    return (c[0], c)


def _map_categories(e: typing.Tuple[str, str], m: typing.Mapping[str, str]) -> typing.Mapping[str, str]:
    if e[0] in m:
        m[e[0]] = m[e[0]] + f'{ORGANIC_NAME_SEPARATOR}{e[1]}'
    else:
        m[e[0]] = e[1]
    return m


def _summarize_organic_categories(categories: typing.Set[str]) -> typing.Mapping[str, str]:
    l = [_split_organic_category(c) for c in categories]
    m = dict()
    for e in l:
        m = _map_categories(e, m)
    return m


def _get_or_add_keyword(session, name: str) -> db_datamodel.Keyword:
    k = session.query(Keyword).filter(Keyword.name == name).first()
    if k is None:
        k = Keyword(name=name)
        session.add(k)
        session.commit()

    return k


def _add_or_update_keywords(session,
                            rss_episode: rss_datamodel.Episode,
                            db_episode: db_datamodel.Episode):
    LOGGER.info(f'Update keywords for episode {rss_episode.title}')
    for idx, k in enumerate(rss_episode.keywords):
        db_keyword = _get_or_add_keyword(session, k)
        db_episode.keywords.append(db_keyword)
    session.commit()


def _render_readme(channel: rss_datamodel.Channel, output_path: pathlib.Path):
    template_folder = (THIS_FILE_FOLDER / '..' / 'template').resolve().absolute()
    file_name = 'README_jinja2.md'

    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_folder)),
    )

    template = environment.get_template(file_name)
    format_date_to_ymd = lambda x: f'{x:%Y-%m-%d}'

    output = template.render(
        {
            'channel': {
                'first_published': format_date_to_ymd(channel.publication_date),
                'last_build': format_date_to_ymd(channel.last_build_date),
                'generation': format_date_to_ymd(datetime.datetime.now()),
            }
        }
    )

    outfile = output_path / 'README.md'
    with open(outfile, 'w') as f:
        f.write(output)


def step_bootstrap():
    currated_categories = poor_mans_csv_parser(THIS_FILE_FOLDER / '..' / '3rd' / 'meta' / 'categories.csv')

    local_feed_file_path = download_current_feed(for_real=True)
    channel_xml = read_feed(local_feed_file_path)
    analysis_result = analyse_channel_data(channel_xml, currated_categories)
    _render_readme(analysis_result.channel, THIS_FILE_FOLDER / '..' / 'docs')
    organic_categories = _summarize_organic_categories(analysis_result.categories)

    _delete_db()

    engine = create_engine(f'sqlite:///{DB_NAME.resolve()}', echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    for c in currated_categories:
        db_cat = Category(
        marker=c.id,
        curated_name=c.name,
        organic_names=organic_categories.get(c.id, '')
        )
        session.add(db_cat)
    session.commit()

    def date_to_str(d: datetime.date) -> str:
        return d.strftime('%Y-%m-%d')

    for idx, rss_episode in enumerate(analysis_result.episodes):
        db_episode = Episode(
            title=rss_episode.title,
            number=rss_episode.number,
            link=rss_episode.link,
            publication_date=date_to_str(rss_episode.publication_date),
            duration_seconds=rss_episode.duration_seconds
        )
        rss_cat = rss_datamodel.Category.curate(currated_categories, rss_episode.category.organic)
        db_cat = session.query(Category).filter(Category.marker == rss_cat.curated_id)[0]
        db_cat.episodes.append(db_episode)

        _add_or_update_keywords(session, rss_episode, db_episode)

        session.add_all([db_episode, db_cat])

    session.commit()


def _generate_graphviz(session):
    raw_lines = [
        'digraph G {',
        '  node [margin=0 fontcolor=blue fontsize=14 shape=box style=filled fillcolor=white]'
    ]

    def start_cluster(c: Category):
        return [
        f'subgraph cluster_{category.lower()}' + ' {',
        f'  label="{r.Category.marker}: {r.Category.currated_name}"',
        f'  bgcolor="lightyellow"'
        ]

    def node_id_from_title(s: str) -> typing.Tuple[str, str]:
        """
        in: A-020: Der Dillenburger Wilhelmsturm: Geschichte - Gegenwart - Zukunft, mit Simon Dietrich [Oranienstadt Dillenburg]

        out: ('A020', 'A=020: Der Dillenburger Wilhelmsturm: Geschichte - Gegenwart - Zukunft, mit Simon Dietrich [Oranienstadt Dillenburg'])
        """
        pairs = s.split(':')
        return (pairs[0].replace('-',''), s)

    def escape(s):
        return s.replace('"', '\\"')

    category = None
    nodes_in_cluster = []
    sql_stmt = select(Category, Episode).join(Episode.category).order_by(Category.marker, Episode.title)
    for idx, r in enumerate(session.execute(sql_stmt)):
        running_category = r.Category.marker

        if category is None:
            category = r.Category.marker
            raw_lines.extend(start_cluster(r.Category))
            nodes_in_cluster = []

        if category != running_category:
            category = r.Category.marker
            if len(nodes_in_cluster) > 1:
                links = ' -> '.join(nodes_in_cluster) + '[style=invis];'
                raw_lines.append(links)
            raw_lines.append('}') # close previous cluster
            raw_lines.extend(start_cluster(r.Category))
            nodes_in_cluster = []

        title_split = node_id_from_title(r.Episode.title)
        raw_lines.append(f'{title_split[0].lower()} [label= "{escape(r.Episode.title)}", URL="{r.Episode.link}"];')
        nodes_in_cluster.append(title_split[0].lower())

    # finish last cluster
    links = ' -> '.join(nodes_in_cluster) + '[style=invis];'
    raw_lines.append(links)
    raw_lines.append('}') # close cluster
    raw_lines.append('')

    if True:
        # episode to episode links
        raw_lines.append('// episode to episode links')
        episodes_by_title_stmt = select(Episode).order_by(Episode.title)

        for db_episode in session.execute(episodes_by_title_stmt):
            from_node_id = node_id_from_title(db_episode.Episode.title)[0].lower()
            for l in db_episode.Episode.linked_episodes:
                # pprint.pprint(f'{db_episode.Episode.title} -> {l.title}')
                to_node_id = node_id_from_title(l.title)[0].lower()
                raw_lines.append(f'{from_node_id} -> {to_node_id} [constraint=false];')

        raw_lines.append('')

    raw_lines.append('}') # close graph
    lines = '\n'.join(raw_lines)
    fn = THIS_FILE_FOLDER / '..' / 'explore' / 'episodes.dot'
    with open(fn, 'w') as fd:
        fd.writelines(lines)


@dataclasses.dataclass
class MarkdownEpisode:
    title: str
    number: int
    link: str
    duration_str: str
    publication_str: str
    keywords: typing.List[str] = dataclasses.field(default_factory=list)
    linked_episodes: typing.List[typing.Tuple[str, str]] = dataclasses.field(default_factory=list)

    def html_link(self):
        return f'[{self.title}]({self.link})'

    def linked_episodes_html(self) -> str:
        s = ''
        for idx, l in enumerate(sorted(self.linked_episodes, key=lambda x: x[0])):
            s += f'**{idx+1:02d}** [{l[0]}]({l[1]})<br/>'
        return s


@dataclasses.dataclass
class MarkdownCategory:
    marker: str
    curated_name: str
    organic_names: typing.List[str]
    episodes: typing.List[MarkdownEpisode]

    def html_anchor_name(self):
        return f'category-{self.marker}'


def _seconds_to_minutes_seconds(sec: int) -> typing.Tuple[int, int]:
    return divmod(sec, 60)


def _render_episode_list(session, output_filepath: pathlib.Path):
    template_folder = (THIS_FILE_FOLDER / '..' / 'template').resolve().absolute()
    file_name = 'episodes_jinja2.md'

    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_folder)),
    )

    template = environment.get_template(file_name)

    def to_markdown_episode(db_episode: Episode) -> MarkdownEpisode:
        minutes, seconds =_seconds_to_minutes_seconds(db_episode.duration_seconds)
        return MarkdownEpisode(
            title=db_episode.title,
            number=db_episode.number,
            link=db_episode.link,
            publication_str=db_episode.publication_date,
            duration_str=f'{minutes:02d}:{seconds:02d}',
            keywords=sorted([k.name for k in db_episode.keywords]),
            linked_episodes=[(l.title, l.link) for l in db_episode.linked_episodes]
        )

    category_stmt = select(Category).order_by(Category.marker)
    md_categories: typing.List[MarkdownCategory] = []
    for r in session.execute(category_stmt):
        md_categories.append(MarkdownCategory(
            marker=r.Category.marker,
            curated_name=r.Category.curated_name,
            organic_names=sorted(r.Category.organic_names.split(ORGANIC_NAME_SEPARATOR)),
            episodes=list(map(to_markdown_episode, r.Category.episodes))
        ))


    output = template.render(
        {
            'categories': md_categories
        }
    )

    LOGGER.info(f'Write to {output_filepath}')
    with open(output_filepath, 'w') as f:
        f.write(output)


@dataclasses.dataclass
class MarkdownKeyword:
    name: str
    appearances: int

def _render_keywords_list(session, output_filepath: pathlib.Path):
    template_folder = (THIS_FILE_FOLDER / '..' / 'template').resolve().absolute()
    file_name = 'keywords_jinja2.md'

    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_folder)),
    )

    template = environment.get_template(file_name)

    keyword_stmt = select(Keyword).order_by(Keyword.name)

    output = template.render(
        {
            'context': [MarkdownKeyword(
                name=r.Keyword.name,
                appearances=len(r.Keyword.episodes)
            )
            for r in session.execute(keyword_stmt)]
        }
    )

    LOGGER.info(f'Write to {output_filepath}')
    with open(output_filepath, 'w') as f:
        f.write(output)


def step_export():
    engine = create_engine(f'sqlite:///{DB_NAME.resolve()}', echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    if True:
        episodes_filepath = THIS_FILE_FOLDER / '..' / 'docs' / 'episodes.md'
        _render_episode_list(session, episodes_filepath)

        keywords_filepath = THIS_FILE_FOLDER / '..' / 'docs' / 'keywords.md'
        _render_keywords_list(session, keywords_filepath)

    if False:
        _generate_graphviz(session)


def step_xlink():
    LOGGER.info('XLINK')
    engine = create_engine(f'sqlite:///{DB_NAME.resolve()}', echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    def categories_ordered_by_marker(session) -> typing.List[Category]:
        stmt = select(Category).order_by(Category.marker)
        return [row.Category for row in session.execute(stmt)]

    def episodes_ordered_by_category(c: Category) -> typing.List[Episode]:
        stmt = select(Category, Episode).join(Episode.category).filter(Category.marker == c.marker).order_by(Episode.title)
        return [row.Episode for row in session.execute(stmt)]

    for _, db_category in enumerate(categories_ordered_by_marker(session)):
        for _, db_episode in enumerate(episodes_ordered_by_category(db_category)):
            LOGGER.info(f'XLink Episode {db_episode.number}, {db_episode.title} link {db_episode.link}')
            raw_links: typing.List[str] = episode_links.get_linked_episodes(db_episode.link)
            for link_str in raw_links:
                stmt = select(Episode).filter(Episode.link == link_str)
                db_linked_episode = session.execute(stmt).fetchone()
                if db_linked_episode:
                    LOGGER.debug(f'   {db_episode.id} {db_episode.link} => {db_linked_episode.Episode.number} {db_linked_episode.Episode.title} link {db_linked_episode.Episode.id} {db_linked_episode.Episode.link}')

                    # TODO(micha): brute force, maybe find appropriate SqlAlchemy solution
                    insert_stmt = Episode_2_episode.insert().values(
                        from_id=db_episode.id,
                        to_id=db_linked_episode.Episode.id)
                    try:
                        session.execute(insert_stmt)
                        session.commit()
                    except Exception as e:
                        LOGGER.error(f'Could not link {db_episode.id} -> {db_linked_episode.Episode.id}: {e}')


                else:
                    LOGGER.error(f'Linked episode not found "{db_episode.link}" => "{link_str}"')



def step_testing():
    LOGGER.info('testing')

    engine = create_engine(f'sqlite:///{DB_NAME.resolve()}', echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    if True:
        # keywords
        LOGGER.info('== Keywords')
        stmt = select(Episode).filter(Episode.id == 42)

        for r in session.execute(stmt):
            pprint.pprint(r.Episode.title)
            for k in sorted(r.Episode.keywords, key=lambda k: k.name):
                pprint.pprint(k.name)

    if True:
        # e 2 e links
        LOGGER.info('== Episode links')
        stmt = select(Episode).filter(Episode.id == 42)
        for r in session.execute(stmt):
            pprint.pprint(f'== {r.Episode.title}')
            for idx, l in enumerate(sorted(r.Episode.linked_episodes, key=lambda e: e.title)):
                pprint.pprint(l.title)

    if True:
        LOGGER.info('== category links')
        stmt = select(Category).order_by(Category.marker).filter(Category.id == 1)
        for r in session.execute(stmt):
            pprint.pprint(f'== {r.Category.curated_name}')
            for e in r.Category.episodes:
                pprint.pprint(e.title)


    pass
