"""
Contains MEMENTO's configuration generator and ``Configuration``, ``Config`` types.
"""

import itertools
from typing import Dict, List

RESERVED_NAMES = ["settings", "runtime"]


def configurations(matrix: dict) -> "Configurations":
    """
    Generate a list of configurations from a configuration matrix. You usually shouldn't need to
    call this directly, as it's called as part of ``Memento.run``. Of course, if you don't want
    to use MEMENTO's runner framework this method can be used completely standalone.
    """

    if not isinstance(matrix, dict):
        raise TypeError(f"matrix must be a dict, got {type(matrix)}")

    if "parameters" not in matrix:
        raise ValueError("matrix must contain a 'parameters' key")

    for name in RESERVED_NAMES:
        if name in matrix["parameters"]:
            raise ValueError(f"`{name}`` is a reserved parameter name")

    parameters = matrix["parameters"]
    settings = matrix.get("settings", {})
    exclude = matrix.get("exclude", [])
    runtime = matrix.get("runtime", {})

    # Generate the cartesian product of all parameters
    elements = itertools.product(*parameters.values())
    configs = [Config(**dict(zip(parameters.keys(), element))) for element in elements]

    # Remove excluded parameter configurations
    for ex in exclude:
        for i, config in enumerate(configs):
            if all(getattr(config, k, _Never) == v for k, v in ex.items()):
                del configs[i]

    return Configurations(configs, settings, runtime)


class Configurations:
    """
    Holds all generated experiment configurations.

    Global settings can be accessed via `configurations.settings`.
    """

    def __init__(self, configs: List["Config"], settings: Dict, runtime: Dict):
        self.configurations = configs
        self.settings = settings
        self.runtime = runtime

        # Create back-references
        for config in self.configurations:
            config.settings = settings
            config.runtime = runtime

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

    def __new__(cls, *args, **kwargs):  # pylint: disable=W0613
        self = super(Config, cls).__new__(cls)
        # This is required to establish the invariant that `_dict` is always defined.
        # During deserialization __getattr__ may be called before __init__. If _dict
        # is not defined this creates an infinite loop.
        self._dict = {}
        return self

    def __init__(self, **kwargs):
        self._dict = kwargs

    def __getattr__(self, name):
        try:
            return self._dict[name]
        except KeyError:
            raise AttributeError(name) from None

    def __repr__(self):
        return self._dict.__repr__()

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, type(self)):
            return False
        return self._dict == o._dict and self.settings == o.settings

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
