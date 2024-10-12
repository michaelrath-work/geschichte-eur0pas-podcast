import dataclasses
import datetime
import typing
import pathlib
import pprint
import xml.etree.ElementTree as ET

NAMESPACES = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}

UNKNOWN_CATEGORY_TAG = '??? UNKOWN_CATEGORY ???'

@dataclasses.dataclass
class Episode:
    category: str
    title: str
    number: int
    link: str
    publication_date: datetime.datetime
    keywords: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class AnalysisResult:
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

def convert_str_to_date(a: any, default: datetime.date = datetime.date(2000, 1,1)) -> int:
    try:
        # e.g. Sat, 12 Oct 2024 02:00:00 +0000
        r = datetime.datetime.strptime(a, '%a, %d %b %Y %H:%M:%S %z')
        return r
    except ValueError:
        print('boing')
        return default
    return default



def analyse_channel_data(channel: ET.Element) -> AnalysisResult:
    categories = set()
    episodes : typing.List[Episode] = []
    for item in channel.findall('item'):
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
                category=category,
                title=title.text or '???',
                number=episode_number,
                publication_date=publication_date,
                link=link,
                keywords=keywords
            )
        )


        categories.add(category)


    return AnalysisResult(
        episodes=episodes,
        categories=categories
    )

def format_episode(e: Episode) -> typing.List[str]:
    return [
        f'### {e.title}\n'
        '| Key | Value | \n'
        '|:----|:------|\n'
        f'|Title | {e.title}|\n',
        f'|Category | {e.category}|\n',
        f'|Puplication date| {e.publication_date:%Y-%m-%d}|\n'
        f'|Episode number|{e.number}|\n'
        f'|Link|{e.link}|\n'
        '\n'
    ]

def format_markdown(p: pathlib.Path, d: AnalysisResult):
    lines = []

    lines.extend([
        '# Geschichte Eur0pas',
        '\n\n'
        'Source https://geschichteeuropas.podigee.io/rssfeed'
        '\n\n'
    ])


    categories_sorted = sorted(list(d.categories))
    lines.extend(
        ['## Categories\n\n',
         '| #  | title | \n',
         '|---:|:----- | \n']
        )
    for i, c in enumerate(categories_sorted):
        lines.append(f'|{i:03d} |{c}|\n')

    lines.extend([
        '\n\n',
        '## Episode list (chronologicaly)\n\n',
    ])
    for e in sorted(d.episodes, key=lambda x: x.title):
        lines.extend(format_episode(e))

    with open(p, mode='w') as f:
        f.writelines(lines)


def main():
    input_p = pathlib.Path('/home/micha') / 'git_root' / 'geschichte-eur0pas-podcast' / 'data' / 'data.xml'
    channel = read_feed(input_p.resolve())
    r = analyse_channel_data(channel)
    output_p = pathlib.Path('/home/micha') / 'git_root' / 'geschichte-eur0pas-podcast' / 'output' / 'episodes.md'
    format_markdown(output_p, r)



if __name__ == '__main__':
    main()