import collections
import datetime
import functools
import pprint
import jinja2
import logging
import pathlib
import os
import typing
import requests
import xml.etree.ElementTree as ET

from rss_datamodel import (
    AnalysisResult,
    Category,
    Channel,
    Episode,
    analyse_channel_data,
    download_current_feed,
    poor_mans_csv_parser,
    read_feed
)


CHANNEL_IMG_URL = 'https://main.podigee-cdn.net/uploads/u10696/804bb26c-c59e-496d-b961-c2531f60dd76.jpg'
PODCAST_URL = 'https://geschichteeuropas.podigee.io/'
URL_FEED_MP3 = os.path.join(PODCAST_URL, 'feed', 'mp3')
THIS_FILE_FOLDER = pathlib.Path(__file__).parent.resolve()
NAMESPACES = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}
UNKNOWN_CATEGORY_TAG = '??? UNKNOWN_CATEGORY ???'
LOGGER = logging.getLogger('main.py')


def read_feed(p: pathlib) -> ET.Element:
    tree = ET.parse(p)
    root = tree.getroot()
    return root.find('channel')


def get_xml_node_text_or_default(e: ET.Element, default: str) -> str:
    if e is not None:
        return e.text
    return default


def convert_str_to_integer(a: any, default: int = -1) -> int:
    try:
        return int(a)
    except ValueError:
        return default


def convert_rss_date_to_date(d: str, default: datetime.date = datetime.date(2000, 1,1)) -> datetime.datetime:
    """
    param d: e.g. Sat, 12 Oct 2024 02:00:00 +0000
    """
    try:
        r = datetime.datetime.strptime(d, '%a, %d %b %Y %H:%M:%S %z')
        return r
    except ValueError:
        return default


def _seconds_to_minutes_seconds(sec: int) -> typing.Tuple[int, int]:
    return divmod(sec, 60)


def select_by_curated_category(c: Category, e: Episode) -> bool:
    return (
        (e.category.curated_id == c.curated_id)
        and (e.category.curated_name == c.curated_name))


def episode_list_per_category(category: Category, analysis_result: AnalysisResult) -> typing.List[str]:
    lines: typing.List[str] = [
            f'<a id="{category.markdown_link_identifier()}"></a>\n'
            f'### {category.curated_str()}\n\n'
        ]

    selected_episodes: typing.List[Episode] = sorted(
        filter(functools.partial(select_by_curated_category, category), analysis_result.episodes),
        key=lambda x: x.title)
    organic_categories = sorted(set([x.category.organic for x in selected_episodes]))
    lines.append(f'[top](#top)\n\n')

    if len(organic_categories) > 1:
        def italic(s: str) -> str:
            return f'*{s}*'

        lines.append(f'Organic categories\n')
        for idx, c in enumerate(organic_categories):
            lines.append(f'{idx+1}. {italic(c)}\n')
        lines.append('\n')


    if len(selected_episodes) > 0:
        lines.extend([
            f'|title |episode | duration (mm:ss) | publication date| keywords |\n',
            '|:---|:---:|---:|---:|:---|\n',
        ])

        for ep in selected_episodes:
            keywords = ', '.join(sorted(ep.keywords))
            min, sec = _seconds_to_minutes_seconds(ep.duration_seconds)
            mm_ss = f'{min:02d}:{sec:02d}'
            lines.append(
                f'|[{ep.title}]({ep.link})|{ep.number:03d}|{mm_ss}|{ep.publication_date:%Y-%m-%d}|{keywords}|\n'
            )
    else:
        lines.append('No episodes found.\n')

    lines.append('\n\n')
    return lines


def keyword_usage(ar: AnalysisResult) -> collections.Counter:
    kws = [
        k.strip() for e in ar.episodes
        for k in e.keywords
    ]
    return collections.Counter(kws)


def format_episodes_as_markdown(p: pathlib.Path,
                                analysis_result: AnalysisResult,
                                adjusted_categories: typing.List[Category]):
    output_lines = ['\n'.join(img_to_link_html(PODCAST_URL, CHANNEL_IMG_URL))]
    output_lines += [
        '\n\n',
        f'<a id="top"></a>\n',
        '# Geschichte Eur0pas',
        '\n'
    ]

    output_lines.extend(
        [
            f'<a id="categories"></a>\n'
            '## Categories\n\n',
            '| id  | curated name | #episodes | organic name |\n',
            '|:---:|:-------------|:---------:|:-------------|\n']
        )

    helper_unschoen = set([(c.curated_id, c.curated_name) for c in adjusted_categories])
    unique_categories = [Category(None, e[0], e[1]) for e in helper_unschoen]

    for category in sorted(unique_categories, key=lambda x: x.curated_id):
        ep: typing.List[Episode] = list(filter(
            functools.partial(select_by_curated_category, category),
            analysis_result.episodes))

        num_episodes = len(ep)
        organic_categories = list(sorted(set([e.category.organic for e in ep])))
        organic_cell = '<br>'.join(organic_categories)
        category_link = f'[{category.curated_str()}](#{category.markdown_link_identifier()})'
        row = f'|{category.curated_id}| {category_link} | {num_episodes:d} | {organic_cell} |\n'
        output_lines.append(row)

    output_lines.extend([
        '\n\n',
        '## Episode list (chronologically)\n\n',
    ])

    for category in sorted(unique_categories, key=lambda x: x.curated_id):
        output_lines.extend(episode_list_per_category(category, analysis_result))

    with open(p, mode='w') as f:
        f.writelines(output_lines)


def format_keywords_as_markdown(p: pathlib.Path,
                                analysis_result: AnalysisResult):

    output_lines = ['\n'.join(img_to_link_html(PODCAST_URL, CHANNEL_IMG_URL))]
    output_lines += [
        '\n\n',
        f'<a id="top"></a>\n',
        '# Used keywords\n\n',
        '\n\n',
        '|keyword| #appearences |     |\n',
        '|:------|-------------:|:---:|\n',
    ]

    ku = keyword_usage(analysis_result)
    for kw in sorted(ku.keys()):
        l = f'|{kw} | {ku[kw]} | [top](#top) |\n'
        output_lines.append(l)

    with open(p, mode='w') as f:
        f.writelines(output_lines)


def download_current_feed(download: bool = True) -> pathlib.Path:
    output_dir = THIS_FILE_FOLDER / '..' / 'rss'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file_path = output_dir / 'rss_feed.xml'

    if download:
        response = requests.get(URL_FEED_MP3)
        with open(output_file_path, 'w') as fd:
            fd.writelines(response.content.decode('utf-8'))

    return output_file_path


def img_to_link_html(url: str, img: str, width=200) -> typing.List[str]:
    return [
        f'<a href="{url}">',
        f'<img src="{img}" alt="{img}" width="{width}">',
        f'</a>'
    ]


def render_readme(channel: Channel, output_path: pathlib.Path):
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


def main():
    LOGGER.info('legacy main')
    predefined_categories = poor_mans_csv_parser(THIS_FILE_FOLDER / '..' / '3rd'/ 'meta' / 'categories.csv')
    local_feed_file_path = download_current_feed()
    channel = read_feed(local_feed_file_path)
    analysis_result = analyse_channel_data(channel, predefined_categories)
    adjusted_categories = list(map(functools.partial(Category.curate, predefined_categories), analysis_result.categories))

    output_path = THIS_FILE_FOLDER / '..' / 'docs'
    output_path.mkdir(parents=True, exist_ok=True)

    render_readme(analysis_result.channel, output_path)
    output_file = output_path / 'episodes.md'

    format_episodes_as_markdown(
        output_file,
        analysis_result,
        adjusted_categories)

    output_file = output_path / 'keywords.md'
    format_keywords_as_markdown(
        output_file,
        analysis_result)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)-15s %(name)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    main()
