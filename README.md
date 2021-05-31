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

Non-HPC tests:

```
$ poetry run pytest
```

HPC tests:

```bash
$ cd slurm-docker-cluster

$ # First run only
$ docker build -t slurm-docker-cluster:20-11-4-1 .
$ bash ./register_cluster.sh

$ docker-compose up -d
$ docker-compose exec -w /memento slurmctld poetry run pytest -m slurm
$ docker-compose down
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
