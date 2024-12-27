import datetime
import logging
import pprint
import pathlib
import typing
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_datamodel import (
    Base,
    Category,
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


def step_bootstrap():
    _delete_db()

    engine = create_engine(f'sqlite:///{DB_NAME.resolve()}', echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    currated_categories = poor_mans_csv_parser(THIS_FILE_FOLDER / '..' / '3rd' / 'meta' / 'categories.csv')

    local_feed_file_path = download_current_feed(for_real=True)
    channel_xml = read_feed(local_feed_file_path)
    analysis_result = analyse_channel_data(channel_xml, currated_categories)
    organic_categories = _summarize_organic_categories(analysis_result.categories)

    for c in currated_categories:
        db_cat = Category(
        marker=c.id,
        currated_name=c.name,
        organic_names=organic_categories.get(c.id, '')
        )
        session.add(db_cat)
    session.commit()

    def date_to_str(d: datetime.date) -> str:
        return d.strftime('%Y-%m-%d')

    for i, e in enumerate(analysis_result.episodes):
        db_episode = Episode(
            title=e.title,
            number=e.number,
            link=e.link,
            publication_date=date_to_str(e.publication_date),
            duration_seconds=e.duration_seconds
        )
        rss_cat = rss_datamodel.Category.adjust(currated_categories, e.category.organic)
        db_cat = session.query(Category).filter(Category.marker == rss_cat.currated_id)[0]
        db_cat.episodes.append(db_episode)
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


def step_export():
    engine = create_engine(f'sqlite:///{DB_NAME.resolve()}', echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    if True:
        _generate_graphviz(session)

    if False:
        sql_stmt = select(Episode).order_by(Episode.title)
        for idx, r in enumerate(session.execute(sql_stmt)):
            linked = episode_links.get_linked_episodes(r.Episode.link)
            LOGGER.info(f'{r.Episode.title} -> {linked}')
            break


def step_xlink():
    LOGGER.info('XLINK')
    engine = create_engine(f'sqlite:///{DB_NAME.resolve()}', echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    if False:
        r = session.execute(select(Episode).filter(Episode.id == 402)).fetchone()
        pprint.pprint(r.Episode.link)
        for e in sorted(r.Episode.linked_episodes, key=lambda e: e.title):
            pprint.pprint(e.title)
        return

    def categories_ordered_by_marker(session) -> typing.List[Category]:
        stmt = select(Category).order_by(Category.marker)
        return [row.Category for row in session.execute(stmt)]

    def episodes_ordered_by_category(c: Category) -> typing.List[Episode]:
        stmt = select(Category, Episode).join(Episode.category).filter(Category.marker == c.marker).order_by(Episode.title)
        return [row.Episode for row in session.execute(stmt)]

    for _, db_category in enumerate(categories_ordered_by_marker(session)):
        # LOGGER.info(f'== Category {db_category.id} {db_category.currated_name}')
        for _, db_episode in enumerate(episodes_ordered_by_category(db_category)):
            LOGGER.info(f'XLink Episode {db_episode.number}, {db_episode.title} link {db_episode.link}')
            raw_links: typing.List[str] = episode_links.get_linked_episodes(db_episode.link)
            # pprint.pprint(f'{db_episode.title} is linked to {raw_links}')
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

            # break
        # break
