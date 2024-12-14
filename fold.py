import functools
import pprint


def a():
    return 10

def b():
    return 3

REGISTRY = {
    'a': a,
    'b': b
}


def update(s: str, l, p):
    if (s == p[0]) or (s == 'ALL'):
        l.append(p[1]())
        return l
    return l



def main():
    # print('hi')
    settings = 'ALL'
    r = functools.reduce(functools.partial(update, settings), REGISTRY.items(), [])
    pprint.pprint(r)

    settings = 'a'
    r = functools.reduce(functools.partial(update, settings), REGISTRY.items(), [])
    pprint.pprint(r)

    settings = 'b'
    r = functools.reduce(functools.partial(update, settings), REGISTRY.items(), [])
    pprint.pprint(r)

if __name__ == '__main__':
    main()