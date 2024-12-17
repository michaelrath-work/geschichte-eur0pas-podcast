import pprint
import re
import typing
import urllib.request


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
    return episode_link_lines


def extract_episode_link(html_line: str):
    match = re.search(r"href=\"(.+)\">", html_line)
    if match:
        return match.group(1)
    return None


def get_linked_episodes(url: str) -> typing.List[str]:
    """
    in: 'https://geschichteeuropas.podigee.io/425-425'

    out: ['https://geschichteeuropas.podigee.io/231-231', 'https://geschichteeuropas.podigee.io/257-257']
    """
    content = get_html_page(url)
    lines = parse_page_content(content)
    return [extract_episode_link(l) for l in lines]


def _dummy_get_content():
    with open('dummy.html', 'r') as f:
        return f.read()

def main():
    content = get_html_page('https://geschichteeuropas.podigee.io/425-425')
    # HELPER to avoid download
    # with open('dummy.html', 'w') as f:
    #     f.write(content)
    # content = _dummy_get_content()
    lines = parse_page_content(content)
    for l in lines:
        pprint.pprint(extract_episode_link(l))

if __name__ == '__main__':
     main()