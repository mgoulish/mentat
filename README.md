# Mentat

Analyse Skupper logs.


See https://deepwiki.com/mgoulish/mentat


## Installation

If you can, install `pyyaml` globally.

If you cannot, use [uv](https://docs.astral.sh/uv/) to set up env:

```
uv pip install -e .
``` 


## Quickstart


```bash
skupper debug dump
```

Move contents of tar file to `./dump`.


```bash
run mentat.py dump/
```

or, if running `uv`:

```bash
uv run mentat.py dump/
```
