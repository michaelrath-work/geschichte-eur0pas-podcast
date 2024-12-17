import datetime
import dataclasses
import os
import pathlib
import pprint
import requests
import typing
import xml.etree.ElementTree as ET

PODCAST_URL = 'https://geschichteeuropas.podigee.io/'

URL_FEED_MP3 = os.path.join(PODCAST_URL, 'feed', 'mp3')

THIS_FILE_FOLDER = pathlib.Path(__file__).parent.resolve()

NAMESPACES = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}

UNKNOWN_CATEGORY_TAG = '??? UNKNOWN_CATEGORY ???'

@dataclasses.dataclass
class CurratedCategory:
    id: str
    name: str


@dataclasses.dataclass
class Category:
    organic: str
    currated_id: str
    currated_name: str

    @staticmethod
    def adjust(categories: typing.List[CurratedCategory], organic: str) -> 'Category':
        # print(f'adjust!!!!!!!!!!!! {categories}')
        CATEGORY_MAP = {i.id: i.name for i in categories}
        # pprint.pprint('+++++++++++++++++++')
        # pprint.pprint(CATEGORY_MAP)
        # pprint.pprint(f'organic {organic}')

        for k, v in CATEGORY_MAP.items():
            if organic[0] == k:
                return Category(organic, k, v)

        return Category(organic, organic, organic)

    def adjusted_str(self):
        return f'{self.currated_id}: {self.currated_name}'

    def markdown_category_link(self) -> str:
        return f'category-{self.currated_id}'


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


def _convert_str_to_integer(a: any, default: int = -1) -> int:
    try:
        return int(a)
    except ValueError:
        return default
    return default

def _convert_str_to_date(a: any, default: datetime.date = datetime.date(2000, 1,1)) -> datetime.datetime:
    try:
        # e.g. Sat, 12 Oct 2024 02:00:00 +0000
        r = datetime.datetime.strptime(a, '%a, %d %b %Y %H:%M:%S %z')
        return r
    except ValueError:
        return default
    return default


def _seconds_to_minutes_seconds(sec: int) -> typing.Tuple[int, int]:
    return divmod(sec, 60)


def _get_xml_node_text_or_default(e: ET.Element, default: str) -> str:
    if e is not None:
        return e.text
    return default


# TODO(micha): shoulb be in separate file
def poor_mans_csv_parser(p: pathlib.Path) -> typing.List[CurratedCategory]:
    r: typing.List[CurratedCategory] = []
    with open(p, 'r') as fd:
        for idx, line in enumerate(fd.readlines()):
            if idx == 0:
                continue
            column_values = [l.strip() for l in line.split(',')]
            r.append(CurratedCategory(column_values[0], column_values[1]))
    return r


def analyse_channel_data(xml_channel: ET.Element, predefined_categories: typing.List[Category]) -> AnalysisResult:
    categories = set()

    channel = Channel(
        _convert_str_to_date(
            xml_channel.find('pubDate').text),
        _convert_str_to_date(
            xml_channel.find('lastBuildDate').text)
    )

    episodes : typing.List[Episode] = []
    for item in xml_channel.findall('item'):
        title = item.find('itunes:title', NAMESPACES)
        organic_category = _get_xml_node_text_or_default(
            item.find('itunes:subtitle', NAMESPACES),
            default=UNKNOWN_CATEGORY_TAG)
        link = _get_xml_node_text_or_default(
            item.find('link'),
            default='??? INCONSISTANT FORMAT ???')
        episode_number = _convert_str_to_integer(
            _get_xml_node_text_or_default(
                item.find('itunes:episode', NAMESPACES),
                default='-1')
            )
        publication_date = _convert_str_to_date(
            _get_xml_node_text_or_default(
                item.find('pubDate'),
                default='??? INCONSISTANT FORMAT ???'))
        keywords_raw = _get_xml_node_text_or_default(
            item.find('itunes:keywords', NAMESPACES),
            default='??? INCONSISTANT FORMAT ???')

        duration_seconds_str = _get_xml_node_text_or_default(
            item.find('itunes:duration', NAMESPACES),
            default='0')

        keywords = ['<p style="background-color:Tomato; color:white;">MISSING</p>']
        if keywords_raw is not None:
            keywords = keywords_raw.split(',')


        category = Category.adjust(predefined_categories, organic_category)

        if title.text.startswith('T-019'):
            pprint.pprint(f'TODO(Micha): invalid organic category format (itunes:subtitle): "{title.text}" != "{organic_category}"')
            category=Category.adjust(predefined_categories, 'T')

        episodes.append(
            Episode(
                category=category,
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

def read_feed(p: pathlib) -> ET.Element:
    tree = ET.parse(p)
    root = tree.getroot()
    return root.find('channel')


def download_current_feed() -> pathlib.Path:
    # response = requests.get(URL_FEED_MP3)
    output_dir = THIS_FILE_FOLDER / '..' / 'rss'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file_path = output_dir / 'rss_feed.xml'

    # with open(output_file_path, 'w') as fd:
        # fd.writelines(response.content.decode('utf-8'))
    return output_file_path
