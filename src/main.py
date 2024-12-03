import collections
import dataclasses
import datetime
import functools
import pathlib
import pprint
import os
import re
import typing
import requests
import xml.etree.ElementTree as ET
import urllib.request


CHANNEL_IMG_URL = 'https://main.podigee-cdn.net/uploads/u10696/804bb26c-c59e-496d-b961-c2531f60dd76.jpg'

PODCAST_URL = 'https://geschichteeuropas.podigee.io/'

URL_FEED_MP3 = os.path.join(PODCAST_URL, 'feed', 'mp3')

THIS_FILE_FOLDER = pathlib.Path(__file__).parent.resolve()

NAMESPACES = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}

UNKNOWN_CATEGORY_TAG = '??? UNKNOWN_CATEGORY ???'

@dataclasses.dataclass
class PredefinedCategory:
    id: str
    name: str


@dataclasses.dataclass
class Category:
    organic: str
    adjusted_id: str
    adjusted_name: str

    @staticmethod
    def adjust(categories: typing.List[PredefinedCategory], organic: str) -> "Category":
        CATEGORY_MAP = {i.id: i.name for i in categories}

        for k, v in CATEGORY_MAP.items():
            if organic[0] == k:
                return Category(organic, k, v)

        return Category(organic, organic, organic)

    def adjusted_str(self):
        return f'{self.adjusted_id}: {self.adjusted_name}'

    def markdown_category_link(self) -> str:
        return f'category-{self.adjusted_id}'


@dataclasses.dataclass
class Episode:
    category: Category
    title: str
    number: int
    link: str
    publication_date: datetime.datetime
    duration_seconds: int
    keywords: typing.List[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Channel:
    publication_date: datetime.datetime
    last_build_date: datetime.datetime


@dataclasses.dataclass
class AnalysisResult:
    channel: Channel
    episodes: typing.List[Episode] = dataclasses.field(default_factory=list)
    categories: typing.Set[str] = dataclasses.field(default_factory=set)


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
    return default

def convert_str_to_date(a: any, default: datetime.date = datetime.date(2000, 1,1)) -> datetime.datetime:
    try:
        # e.g. Sat, 12 Oct 2024 02:00:00 +0000
        r = datetime.datetime.strptime(a, '%a, %d %b %Y %H:%M:%S %z')
        return r
    except ValueError:
        return default
    return default


def _seconds_to_minutes_seconds(sec: int) -> typing.Tuple[int, int]:
    return divmod(sec, 60)

def analyse_channel_data(xml_channel: ET.Element, predefined_categories: typing.List[Category]) -> AnalysisResult:
    categories = set()

    channel = Channel(
        convert_str_to_date(
            xml_channel.find('pubDate').text),
        convert_str_to_date(
            xml_channel.find('lastBuildDate').text)
    )

    episodes : typing.List[Episode] = []
    for item in xml_channel.findall('item'):
        title = item.find('itunes:title', NAMESPACES)
        organic_category = get_xml_node_text_or_default(
            item.find('itunes:subtitle', NAMESPACES),
            default=UNKNOWN_CATEGORY_TAG)
        link = get_xml_node_text_or_default(
            item.find('link'),
            default='??? INCONSISTANT FORMAT ???')
        episode_number = convert_str_to_integer(
            get_xml_node_text_or_default(
                item.find('itunes:episode', NAMESPACES),
                default='-1')
            )
        publication_date = convert_str_to_date(
            get_xml_node_text_or_default(
                item.find('pubDate'),
                default='??? INCONSISTANT FORMAT ???'))
        keywords_raw = get_xml_node_text_or_default(
            item.find('itunes:keywords', NAMESPACES),
            default='??? INCONSISTANT FORMAT ???')

        duration_seconds_str = get_xml_node_text_or_default(
            item.find('itunes:duration', NAMESPACES),
            default='0')

        keywords = ['<p style="background-color:Tomato; color:white;">MISSING</p>']
        if keywords_raw is not None:
            keywords = keywords_raw.split(',')

        episodes.append(
            Episode(
                category=Category.adjust(predefined_categories, organic_category),
                title=title.text or '???',
                number=episode_number,
                publication_date=publication_date,
                link=link,
                duration_seconds=int(duration_seconds_str),
                keywords=keywords
            )
        )

        categories.add(organic_category)

    return AnalysisResult(
        channel=channel,
        episodes=episodes,
        categories=categories
    )


def select_by_adjusted_category(c: Category, e: Episode) -> bool:
    return (
        (e.category.adjusted_id == c.adjusted_id)
        and (e.category.adjusted_name == c.adjusted_name))


def episode_list_per_category(category: Category, analysis_result: AnalysisResult) -> typing.List[str]:
    lines: typing.List[str] = [
            f'<a id="{category.markdown_category_link()}"></a>\n'
            f'### {category.adjusted_str()}\n\n'
        ]

    selected_episodes: typing.List[Episode] = sorted(
        filter(functools.partial(select_by_adjusted_category, category), analysis_result.episodes),
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
        '\n\n'
    ]
    output_lines +=[
        '\n\n'
        f'Data source: {URL_FEED_MP3}'
        '\n\n'
    ]

    now = datetime.datetime.now()
    format_date_to_ymd = lambda x: f'{x:%Y-%m-%d}'
    output_lines.extend('## Meta\n\n')
    output_lines.extend('|key |value|\n')
    output_lines.extend('|:---|:----|\n')
    output_lines.extend(f'|podcast first published|{format_date_to_ymd(analysis_result.channel.publication_date)}|\n')
    output_lines.extend(f'|podcast last build|{format_date_to_ymd(analysis_result.channel.last_build_date)}|\n')
    output_lines.extend(f'|date of generation of this list|{format_date_to_ymd(now)}|\n')
    output_lines.extend('\n')

    output_lines.extend(
        [
            f'<a id="categories"></a>\n'
            '## Categories\n\n',
            '| id  | curated name | #episodes | organic name |\n',
            '|:---:|:-------------|:---------:|:-------------|\n']
        )

    organic_categories_sorted = sorted(adjusted_categories, key= lambda x: x.organic)

    for idx, cat in enumerate(organic_categories_sorted):
        ep: typing.List[Episode] = list(filter(
            functools.partial(select_by_adjusted_category, cat),
            analysis_result.episodes))
        num_episodes = len(ep)
        category_link = f'[{cat.adjusted_str()}](#{cat.markdown_category_link()})'
        output_lines.append(f'|{cat.adjusted_id}| {category_link} | {num_episodes:d} | {cat.organic} |\n')

    helper_unschoen = set([(c.adjusted_id, c.adjusted_name) for c in adjusted_categories])
    unique_categories = [Category(None, e[0], e[1]) for e in helper_unschoen]

    output_lines.extend([
        '\n\n',
        '## Keywords \n\n',
        'List of all used [keywords](keywords.md)\n\n'
    ])

    output_lines.extend([
        '\n\n',
        '## Episode list (chronologically)\n\n',
    ])

    for category in sorted(unique_categories, key=lambda x: x.adjusted_id):
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
        '[Episode list](episodes.md)\n\n',
        '|keyword| #appearences |     |\n',
        '|:------|-------------:|:---:|\n',
    ]

    ku = keyword_usage(analysis_result)
    for kw in sorted(ku.keys()):
        l = f'|{kw} | {ku[kw]} | [top](#top) |\n'
        output_lines.append(l)

    with open(p, mode='w') as f:
        f.writelines(output_lines)


def download_current_feed() -> pathlib.Path:
    response = requests.get(URL_FEED_MP3)
    output_dir = THIS_FILE_FOLDER / '..' / 'data'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file_path = output_dir / 'data.xml'

    with open(output_file_path, 'w') as fd:
        fd.writelines(response.content.decode('utf-8'))
    return output_file_path


def poor_mans_csv_parser(p: pathlib.Path) -> typing.List[PredefinedCategory]:
    r: typing.List[PredefinedCategory] = []
    with open(p, 'r') as fd:
        for idx, line in enumerate(fd.readlines()):
            if idx == 0:
                continue
            column_values = [l.strip() for l in line.split(',')]
            r.append(PredefinedCategory(column_values[0], column_values[1]))
    return r


def img_to_link_html(url: str, img: str, width=200) -> typing.List[str]:
    return [
        f'<a href="{url}">',
        f'<img src="{img}" alt="{img}" width="{width}>',
        f'</a>'
    ]

def main():
    predefined_categories = poor_mans_csv_parser(THIS_FILE_FOLDER / '..' / 'meta' / 'categories.csv')
    local_feed_file_path = download_current_feed()
    channel = read_feed(local_feed_file_path)
    analysis_result = analyse_channel_data(channel, predefined_categories)
    adjusted_categories = list(map(functools.partial(Category.adjust, predefined_categories), analysis_result.categories))
    output_path = THIS_FILE_FOLDER / '..' / 'output'
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / 'episodes.md'

    format_episodes_as_markdown(
        output_file,
        analysis_result,
        adjusted_categories)

    output_file = output_path / 'keywords.md'
    format_keywords_as_markdown(
        output_file,
        analysis_result)


def get_html_page(url: str):
    with urllib.request.urlopen(url) as response:
        page_bytes = response.read()
        content = page_bytes.decode('utf-8')
        return content

def parse_page_content(content: str):
    lines = content.split('\n')
    state = 'SEARCHING'
    episode_link_lines = []
    line_nr = 0
    while line_nr < len(lines):
        current_line = lines[line_nr].strip()
        if (state == 'SEARCHING') and (current_line.find('<p><strong>Verknüpfte Folgen') >= 0):
            state = 'SCAN'
        elif (state == 'SCAN'):
            if current_line.find('<p><strong>') < 0:
                episode_link_lines.append(current_line)
            else:
                line_nr = len(lines)
        line_nr +=1
    # pprint.pprint(episode_link_lines)
    return episode_link_lines


def extract_episode_link(html_line: str):
    match = re.search(r"href=\"(.+)\">", html_line)
    if match:
        return match.group(1)
    return None

def _dummy_get_content():
    with open('dummy.html', 'r') as f:
            return f.read()

def main2():
    print('hi')
    content = get_html_page('https://geschichteeuropas.podigee.io/425-425')

    # HELPER to avoid download
    # with open('dummy.html', 'w') as f:
    #     f.write(content)
    # content = _dummy_get_content()
    lines = parse_page_content(content)
    for l in lines:
        pprint.pprint(extract_episode_link(l))

if __name__ == '__main__':
    # main()
    main2()