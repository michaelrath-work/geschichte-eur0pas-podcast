import dataclasses
import datetime
import pathlib
import pprint
import typing
import requests
import xml.etree.ElementTree as ET

MP3_FEED_URL = 'https://geschichteeuropas.podigee.io/feed/mp3'

THIS_FILE_FOLDER = pathlib.Path(__file__).parent.resolve()

NAMESPACES = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}

UNKNOWN_CATEGORY_TAG = '??? UNKNOWN_CATEGORY ???'

@dataclasses.dataclass
class Category:
    organic: str
    adjusted: str

    @staticmethod
    def adjust_category(organic: str) -> "Category":
        A = 'A: Epochenübergreifende Themen'
        N = 'N: Absolutismus und Aufklärung'
        O = 'O: Zeitalter der Revolutionen'
        T = 'T: Kalter Krieg und europäische Einigung'
        X = 'X: Geschichtswissenschaft und Erinnerungskultur'
        Y = 'Y: Quellen'
        MAPPING = {
            'A - Epochen': A,
            'A; Epochen': A,
            'A: Epochen': A,

            'N: Absolutimus und Aufklärung': N,

            'O: Das Zeitalter der Revolutionen': O,

            'T: Kalter Krieg': T,
            'Kalter Krieg': T,

            'W: Geschichtswissenschaft und Erinnerungskultur': X,
            'X: Geschichtswissenschaft und': X,

            'Y: Quelle': Y,
            'Y - Quellen': Y,
            'Y; Quellen': Y,
        }

        for k, v in MAPPING.items():
            if organic.startswith(k):
                return Category(organic, v)

        return Category(organic, organic)

    @staticmethod
    def markdown_category_link(s: str) -> str:
        return f'category-{s}'

    def identifier(s: str) -> str:
        g = s.split(':')
        if len(g) > 1:
            return g[0].strip()
        return '?'


@dataclasses.dataclass
class Episode:
    organic_category: str
    adjusted_category: str
    title: str
    number: int
    link: str
    publication_date: datetime.datetime
    keywords: typing.List[str] = dataclasses.field(default_factory=list)

    @staticmethod
    def adjust_category(e: "Episode") -> "Episode":
        e.adjusted_category = Category.adjust_category(e.organic_category).adjusted
        return e


@dataclasses.dataclass
class DefinedCategory:
    id: str
    name: str

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



def analyse_channel_data(xml_channel: ET.Element) -> AnalysisResult:
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
        category = get_xml_node_text_or_default(
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

        keywords = ['??? INCONSISTANT FORMAT ???']
        if keywords_raw is not None:
            keywords = keywords_raw.split(',')

        episodes.append(
            Episode(
                organic_category=category,
                adjusted_category=category,
                title=title.text or '???',
                number=episode_number,
                publication_date=publication_date,
                link=link,
                keywords=keywords
            )
        )


        categories.add(category)

    return AnalysisResult(
        channel=channel,
        episodes=episodes,
        categories=categories
    )

def format_markdown(p: pathlib.Path,
                    analysis_result: AnalysisResult,
                    categories: typing.List[Category], episodes: typing.List[Episode]):
    lines = []
    lines.extend([
        f'<a id="top"></a>\n',
        '# Geschichte Eur0pas',
        '\n\n'
        f'Data source for this overview is {MP3_FEED_URL}'
        '\n\n'
    ])

    now = datetime.datetime.now()
    format_date_to_ymd = lambda x: f'{x:%Y-%m-%d}'
    lines.extend('## Meta\n\n')
    lines.extend('|key |value|\n')
    lines.extend('|:---|:----|\n')
    lines.extend(f'|podcast first published|{format_date_to_ymd(analysis_result.channel.publication_date)}|\n')
    lines.extend(f'|podcast last build|{format_date_to_ymd(analysis_result.channel.last_build_date)}|\n')
    lines.extend(f'|date of generation of this list|{format_date_to_ymd(now)}|\n')
    lines.extend('\n')

    lines.extend(
        [
            f'<a id="categories"></a>\n'
            '## Categories\n\n',
            '| #  | marker |title (organic)| title (re-categorized by MR)| #episodes |\n',
            '|---:|:---:|:---------------|:-------------|:---:|\n']
        )
    categories_sorted = sorted(categories, key= lambda x: x.organic)

    unique_categories = set([x.adjusted for x in categories])

    for i, cat in enumerate(categories_sorted):
        category_link = f'[{cat.adjusted}](#{Category.markdown_category_link(Category.identifier(cat.adjusted))})'
        category_id = Category.identifier(cat.adjusted)
        ep: typing.List[Episode] = list(filter(lambda x: x.adjusted_category == cat.adjusted, episodes))
        num_episodes = len(ep)
        # print(f'episodes for {cat.adjusted}, {num_episodes}')
        lines.append(f'|{i:03d} | {category_id} | {cat.organic}| {category_link} | {num_episodes:d} |\n')

    lines.extend([
        '\n\n',
        '## Episode list (chronologically)\n\n',
    ])

    for adjusted_category in sorted(unique_categories):
        lines.extend([
            f'<a id="{Category.markdown_category_link(Category.identifier(adjusted_category))}"></a>\n'
            f'### {adjusted_category}\n\n'
        ])

        selected_episodes: typing.List[Episode] = sorted(
            filter(lambda x: x.adjusted_category == adjusted_category, episodes),
        key=lambda x: x.title)
        organic_categories = sorted(set([x.organic_category for x in selected_episodes]))

        lines.append(f'[Top](#top)\n\n')

        if (len(organic_categories) > 1) or (adjusted_category not in organic_categories):
            def italic(s: str) -> str:
                return f'*{s}*'

            lines.append(f'Organic categories\n')
            for idx, c in enumerate(organic_categories):
                lines.append(f'{idx+1}. {italic(c)}\n')
            lines.append('\n')


        lines.extend([
            f'|title |episode | publication date| keywords |\n',
            '|---|---|---|---|\n',
        ])

        for ep in selected_episodes:
            keywords = ', '.join(sorted(ep.keywords))
            lines.append(
                f'|[{ep.title}]({ep.link})|{ep.number:03d}|{ep.publication_date:%Y-%m-%d}|{keywords}|\n'
            )

        lines.append('\n\n')

    with open(p, mode='w') as f:
        f.writelines(lines)


def download_current_feed() -> pathlib.Path:
    response = requests.get(MP3_FEED_URL)
    output_dir = THIS_FILE_FOLDER / '..' / 'data'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file_path = output_dir / 'data.xml'

    with open(output_file_path, 'w') as fd:
        fd.writelines(response.content.decode('utf-8'))
    return output_file_path


def poor_mans_csv_parser(p: pathlib.Path) -> typing.List[DefinedCategory]:
    r: typing.List[DefinedCategory] = []
    with open(p, 'r') as fd:
        for idx, line in enumerate(fd.readlines()):
            if idx == 0:
                continue
            column_values = [l.strip() for l in line.split(',')]
            r.append(DefinedCategory(column_values[0], column_values[1]))
    return r


def main():
    local_feed_file_path = download_current_feed().resolve()
    channel = read_feed(local_feed_file_path)
    r = analyse_channel_data(channel)
    mapped_categories = list(map(Category.adjust_category, r.categories))

    output_path = THIS_FILE_FOLDER / '..' / 'output'
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / 'episodes.md'

    episodes = list(map(Episode.adjust_category, r.episodes))

    format_markdown(output_file,
                    r,
                    mapped_categories, episodes)


if __name__ == '__main__':
    main()
