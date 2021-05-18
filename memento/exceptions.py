"""
Exceptions raised by Memento.
"""


from memento.configurations import Config


class CacheMiss(Exception):
    """
    Raised when ``force_cache=True`` is passed to ``Memento.run`` and an experiment was not found
    in the cache.
    """

    def __init__(self, config: Config) -> None:
        super().__init__(f"Config {config} was not found in the cache")


class CyclicDependency(Exception):
    """
        Raised when ``run_all`` is called with a cyclic dependency in one or more of the matrices.
    """

    def __init__(self) -> None:
        super().__init__(f"Cyclic dependency detected")
