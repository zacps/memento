"""
Contains `Memento`, the main entry point of MEMENTO.
"""

from typing import Any, Callable, List

from memento.parallel import TaskManager, delayed
from memento.caching import MemoryCacheProvider
from memento.configurations import configurations


class Memento:  # pylint: disable=R0903
    """
    The main entry point of MEMENTO.
    """

    def __init__(self, func: Callable):
        self.func = func

    def run(self, matrix: dict) -> List[Any]:
        """
        Run a configuration matrix and return it's results.
        """

        configs = configurations(matrix)

        # TODO: This should be a filesystem backed cache
        cache = MemoryCacheProvider()
        manager = TaskManager()

        results = [None] * len(configs)

        for i, config in enumerate(configs):
            try:
                results[i] = cache.get(config)
            except KeyError:
                # TODO: We should pass in a context object so the user's code can interact with
                # memento in a task.
                manager.add_task(delayed(self.func)(config))

        others = manager.run()[::-1]

        for i in range(len(results)):  # pylint: disable=C0200
            if results[i] is None:
                results[i] = others.pop()

        # TODO: We should return an object which provides metadata about this run here.
        # Things we want:
        # * Was a particular result cached or run?
        # * How long did a result take to run?
        # * What was the memory usage of a particular run?
        return results
