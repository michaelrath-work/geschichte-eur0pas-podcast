# Geschichte Eur0pas Podcast

This project sorts podcast episodes of https://geschichteeuropas.podigee.io/ in chronological order, because some podcast catcher apps have trouble with subtiles (schema `[A_Z]-[0-9]{3}`) and ordering.
According to original author https://geschichteeuropas.podigee.io/ podcast episodes should be listened like this (German)

> "Die Episoden werden thematisch und nicht nach Erscheinungsdatum nummeriert. Für einen chronologischen Durchgang zur europäischen Geschichte sollten die Episoden nach Namen sortiert werden." [1](#ref1)

Translation (generated)
> "The episodes are numbered thematically and not by release date. For a chronological passage to European history, the episodes should be sorted by name."

The script takes the published RSS feed [2](#ref2) as input and outputs recommended ordering.
It also tries to fix some typos (e.g. category naming), but otherwise podcast content is not altered (changes are marked).

Example is shown here [Episodes](output/episodes.md)


## How to use

1. Grab feed from https://geschichteeuropas.podigee.io/feed/mp3
2. Save as `data/data.xml` in this project
3. Run `python3 src/main.py`
4. Output can be found in [Episodes](output/episodes.md)

## TODO

Directly download feed and thus avoid steps 1 and 2 in [How to use](#how-to-use)


## References / Links

<a id="ref1"></a>
[1] https://geschichteeuropas.podigee.io/

<a id="ref1"></a>
[2] https://geschichteeuropas.podigee.io/#subscribe


