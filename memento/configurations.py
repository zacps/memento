"""
Contains MEMENTO's main entrypoint, `run`, and the configuration generator.
"""

import itertools


def run(matrix: dict):
    """
    The main entry point of MEMENTO.

    `matrix` describes the list of experiments you want MEMENTO to run. This must contain a key
    `parameters` which is itself a dict, this describes each paramter you want to vary for your
    experiments and their values.

    As an example let's say you wanted to test a few simple linear classifiers on a number of
    image recognition datasets. You might write something like this:

    .. note::
        Don't worry if you're not working on machine learning, this is just an example.

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

    MEMENTO would then generate 12 configurations by taking the *cartesian product* of the
    parameters.

    ### Global Settings

    Frequently you might also want to set some global configuration values, such as a regularization
    parameter or potentially even change your preprocessing pipeline. In this case MEMENTO also
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

    ### Excluding Combinations

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
    """

    if not isinstance(matrix, dict):
        raise TypeError(f"matrix must be a dict, got {type(matrix)}")

    if "parameters" not in matrix:
        raise ValueError("matrix must contain a 'parameters' key")

    parameters = matrix["parameters"]
    settings = matrix.get("settings", {})
    exclude = matrix.get("exclude", [])

    # Generate the cartesian product of all parameters
    elements = itertools.product(*parameters.values())
    configurations = [
        Config(**dict(zip(parameters.keys(), element))) for element in elements
    ]

    for ex in exclude:
        for i, config in enumerate(configurations):
            if all(getattr(config, k, _Never) == v for k, v in ex.items()):
                del configurations[i]

    return Configurations(configurations, settings)


class Configurations:
    """
    Holds all generated experiment configurations.

    Global settings can be accessed via `configurations.settings`.
    """

    def __init__(self, configurations, settings):
        self.configurations = configurations
        self.settings = settings

        # Create back-references
        for config in self.configurations:
            config.settings = settings

    def __len__(self):
        return self.configurations.__len__()

    def __iter__(self):
        return self.configurations.__iter__()

    def __getitem__(self, index):
        return self.configurations.__getitem__(index)


class Config:
    """
    A single experiment configuration. Parameters are set as attributes.

    Global settings can also be accessed via `config.settings`.
    """

    def __init__(self, **kwargs):
        self._dict = kwargs

    def __getattr__(self, name):
        return self._dict[name]

    def _set(self, name, value):
        self._dict[name] = value

    def asdict(self):
        """
        Return the internal `dict` of parameters.
        """

        return self._dict


class _Never:  # pylint: disable=R0903
    """
    Type used for hackish equality test (it should always fail, as this should never be
    constructed).
    """

    def __init__(self) -> None:
        raise Exception("_Never cannot be constructed")
