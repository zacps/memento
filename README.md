# Memento

Memento is a Python library for running computationally expensive experiments. 

If you need to run a large number of time-consuming experiments Memento can help:
* Structure your configuration
* Parallelize experiments across CPUs
* Save and restore results
* Checkpoint in-progress experiments
* Send notifications when experiments fail or finish

## Getting Started

### Install

Memento is not yet available from PyPi. Instead, see the instructions for [Developing](#Developing) to install the current development version.

### The Configuration Matrix

The core of Memento is a configuration `matrix` that describes the list of experiments you
want Memento to run. This must contain a key `parameters` which is itself a dict, this describes
each paramter you want to vary for your experiments and their values.

As an example let's say you wanted to test a few simple linear classifiers on a number of
image recognition datasets. You might write something like this:

> Don't worry if you're not working on machine learning, this is just an example.

```python
matrix = {
  "parameters": {
    "model": [
      sklearn.svm.SVC,
      sklearn.linear_model.Perceptron,
      sklearn.linear_model.LogisticRegression
    ],
    "dataset": ["imagenet", "mnist", "cifar10", "quickdraw"]
  }
}
```

Memento would then generate 12 configurations by taking the *cartesian product* of the
parameters.

Frequently you might also want to set some global configuration values, such as a regularization
parameter or potentially even change your preprocessing pipeline. In this case Memento also
accepts a "settings" key. These settings apply to all experiments and can be accessed from the
configuration list as well as individual configurations.

```python
matrix = {
  "parameters": ...,
  "settings": {
    "regularization": 1e-1,
    "preprocessing": make_preprocessing_pipeline()
  }
}
```

You can also exclude specific parameter configurations. Returning to our machine learning
example, if you know SVCs perform poorly on cifar10 you might decide to skip that
experiment entirely. This is done with the "exclude" key:

```python
matrix = {
  "parameters": ...,
  "exclude": [
    {"model": sklearn.svm.SVC, "dataset": "cifar10"}
  ]
}
```

### Running an experiment

Along with a configuration matrix you need some code to run your experiments. This can be any
`Callable` such as a function, lambda, class, or class method.

```python
from memento import Memento, Config, Context

def experiment(context: Context, config: Config):
  classifier = config.model()
  dataset = fetch_dataset(config.dataset)

  classifier.fit(*dataset)

  return classifier

Memento(experiment).run(matrix)
```

You can also perform a dry run to check you've gotten the matrix correct.

```python
Memento(experiment).run(matrix, dry_run=True)
```

```python
Running configurations:
  {'model': sklearn.svm.SVC, 'dataset': 'imagenet'}
  {'model': sklearn.svm.SVC, 'dataset': 'mnist'}
  {'model': sklearn.svm.SVC, 'dataset': 'cifar10'}
  {'model': sklearn.svm.SVC, 'dataset': 'quickdraw'}
  {'model': sklearn.linear_model.Perceptron, 'dataset': 'imagenet'}
  ...
Exiting due to dry run
```

<h2 id="Developing">Developing</h2>

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
$ # New version
$ docker build -t memento-slurm -f Dockerfile.memento  ..

$ docker-compose up -d
$ docker-compose exec -w /memento slurmctld poetry run pytest -m slurm
$ docker-compose down
```

### Linters

```
$ poetry run pylint memento && poetry run black .
```

### Build Documentation

```
$ poetry run sphinx-apidoc -o docs memento -f
$ poetry run sphinx-build -W -b html docs docs/_build
```

### Run CI locally

Install [act](https://github.com/nektos/act), then:

```
$ act
```

## Roadmap

* Finish HPC support
* Improve result serialisation
* Production testing & fleshed-out integration test suite
* Public release

## Contributors

* [Zac Pullar-Strecker](https://github.com/zacps)
* [Feras Albaroudi](https://github.com/NeedsSoySauce)
* [Liam Scott-Russell](https://github.com/Liam-Scott-Russell)
* [Joshua de Wet](https://github.com/Dewera)
* [Nipun Jasti](https://github.com/watefeenex)
* [James Lamberton](https://github.com/JamesLamberton)
* Joerg Wicker

## License

Memento is licensed under the [BSD+Patent](https://opensource.org/licenses/BSDplusPatent) license. This is a modified version of the [BSD](https://opensource.org/licenses/BSD-3-Clause) license which includes a patent grant.
