<!-- automate this nonsense, i.e. use generate Readme.md as well -->
<a href="https://geschichteeuropas.podigee.io/">
  <img src="https://main.podigee-cdn.net/uploads/u10696/804bb26c-c59e-496d-b961-c2531f60dd76.jpg" alt="link to geschichte europas images" width="200">,
</a>

# Geschichte Eur0pas Podcast

This project sorts podcast episodes of https://geschichteeuropas.podigee.io/ in chronological order, because some podcast catcher apps have trouble with subtiles and ordering.
According to original author/creator Tobias Jakobi [[1]](#ref1) podcast episodes [[2]](#ref2) are supposed to be listened in this order

> (German quote) "Die Episoden werden thematisch und nicht nach Erscheinungsdatum nummeriert. Für einen chronologischen Durchgang zur europäischen Geschichte sollten die Episoden nach Namen sortiert werden."

> (English translation) "The episodes are numbered thematically and not by release date. For a chronological passage to European history, the episodes should be sorted by name."

This script takes the published RSS feed [[3]](#ref3) as input and outputs the recommended ordering.
It also tries to fix some typos (e.g. category naming), but otherwise podcast content is not altered.
Changes are marked, i.e. when there are differences between **organic** (the original RSS feed) and changes made by author of this program.

An example output (maybe out of date) is shown here [output/episodes.md](output/episodes.md)


## How to use (legacy)

1. Execute `python3 src/main.py`
2. Output is written to this location [Episodes (output/episodes.md)](output/episodes.md)

## How to use (TNG)

1. `python3 src/main_tng.py bootstrap`
2. `python3 src/main_tng.py xlink`
3. `python3 src/main_tng.py export`
4. temporary: `dot -Tsvg explore/episodes.dot -o explore/episodes.svg` see [Readme](explore/Readme.md)

## TODO

Experimental (currently insane, propably not usable) [episode link visualization](explore/episodes.svg)


## References / Links

<a id="ref1"></a>
[1] https://geschichteeuropas.podigee.io/imprint

<a id="ref2"></a>
[2] https://geschichteeuropas.podigee.io/

<a id="ref3"></a>
[3] https://geschichteeuropas.podigee.io/#subscribe


