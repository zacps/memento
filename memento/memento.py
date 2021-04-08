"""
Contains `Memento`, the main entry point of MEMENTO.
"""

import logging
from typing import Any, Callable, List, Optional

from memento.parallel import TaskManager, delayed
from memento.caching import Cache
from memento.configurations import configurations

logger = logging.getLogger(__name__)


class Memento:  # pylint: disable=R0903
    """
    The main entry point of MEMENTO.
    """

    def __init__(self, func: Callable):
        self.func = func

    def run(self, matrix: dict, dry_run: bool = False) -> Optional[List[Any]]:
        """
        Run a configuration matrix and return it's results.
        """

        configs = configurations(matrix)

        logger.info("Running configurations:")
        for config in configs:
            logger.info("  %s", config)

        if dry_run:
            logger.info("Exiting due to dry run")
            return None

        cache = Cache(self.func)
        manager = TaskManager()

        results = [None] * len(configs)

        for i, config in enumerate(configs):
            try:
                results[i] = cache(config, force_cache=True)
            except KeyError:
                # TODO: We should pass in a context object so the user's code can interact with
                # memento in a task.
                manager.add_task(delayed(cache)(config))

        n_cached = len([result for result in results if result is not None])
        logger.info("%s/%s results retrieved from cache", n_cached, len(configs))

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
