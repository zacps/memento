# MEMENTO

MEMENTO is a Python library for running computationally expensive experiments.

## Developing

### Install dependencies

```
$ pip install poetry
$ poetry install
```

### Add dependencies

```
$ poetry add (--dev) fancy_library
```

### Tests

```
$ poetry run pytest
```

Alternatively to only run a subset of tests that haven't been marked as time consuming/slow you can use:

```
$ poetry run pytest -m "not slow"
```

### Linters

```
$ poetry run pylint memento && poetry run black .
```

### Run CI locally

Install [act](https://github.com/nektos/act), then:

```
$ act
```

## Project Proposal Document

https://docs.google.com/document/d/1_Jbsl_W1Cttgn7ndZmY0vd5OfwdPE2OyH1HOZ6utj5k/edit
