<a href="https://geschichteeuropas.podigee.io/">
  <img src="https://main.podigee-cdn.net/uploads/u10696/804bb26c-c59e-496d-b961-c2531f60dd76.jpg" alt="link to geschichte europas images" width="200">,
</a>

# Geschichte Eur0pas Podcast

Description and output can be found [here](https://michaelrath-work.github.io/geschichte-eur0pas-podcast/).

## For developers

### How to use (legacy)

1. Execute `python3 src/main.py`
2. Output is written to this location [Episodes (docs/episodes.md)](docs/episodes.md)

### How to use (TNG)

1. `python3 src/main_tng.py bootstrap`
2. `python3 src/main_tng.py xlink`
3. `python3 src/main_tng.py export`
4. temporary: `dot -Tsvg explore/episodes.dot -o explore/episodes.svg` see [Readme](explore/Readme.md)

## TODO

Experimental (currently insane, probably not usable) [episode link visualization](explore/episodes.svg)

