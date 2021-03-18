"""
Contains MEMENTO's main entrypoint, `run`, and the configuration generator.
"""

import itertools


def run(matrix: dict):
    """
    The main entry point of MEMENTO.
    """

    if not isinstance(matrix, dict):
        raise ValueError(f"matrix must be a dict, got {type(matrix)}")

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
    A single experiment configuration. Parameters are set as read-only attributes.

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
