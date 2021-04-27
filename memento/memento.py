"""
Contains `Memento`, the main entry point of MEMENTO.
"""

import functools
import logging
from datetime import datetime
from typing import Any, Callable, List, Optional

import cloudpickle

from memento.parallel import TaskManager, delayed
from memento.caching import Cache, FileSystemCacheProvider
from memento.configurations import configurations, Config
from memento.task_interface import Context, Result

logger = logging.getLogger(__name__)


class Memento:  # pylint: disable=R0903
    """
    The main class of MEMENTO. This is the 'front end' of MEMENTO with which you can run a
    configuration matrix and retrieve results from your experiments.
    """

    def __init__(self, func: Callable):
        """
        :param func: Your experiment code. This will be called with an experiment configuration.
        """
        self.func = func

    def run(self, matrix: dict, dry_run: bool = False) -> Optional[List[Result]]:
        """
        Run a configuration matrix and return it's results.

        :param matrix: A configuration matrix
        :param dry_run: Do not actually run experiments, just log what would be run
        :returns: A list of results from your experiments.
        """

        configs = configurations(matrix)

        logger.info("Running configurations:")
        for config in configs:
            logger.info("  %s", config)

        if dry_run:
            logger.info("Exiting due to dry run")
            return None

        cache = FileSystemCacheProvider(key=_key)
        manager = TaskManager()

        # Run tasks for which we have no cached result
        ran = set()
        for config in configs:
            key = _key(self.func, config)
            if not cache.contains(key):
                context = Context(key)
                manager.add_task(delayed(_wrapper(self.func)(context, config)))
                ran.add(config)

        manager.run()

        results = [cache.get(_key(self.func, config)) for config in configs]

        for result in results:
            if result.config in ran:
                result.was_cached = False

        logger.info(
            "%s/%s results retrieved from cache",
            len(configs) - len(ran),
            len(configs),
        )

        return results


def _wrapper(func: Callable) -> Callable:
    """
    Wrapper which runs in the task thread. This is responsible for collecting performance metrics and writing to the cache.
    """

    @functools.wraps(func)
    def inner(context: Context, config: Config) -> Result:
        start_time = datetime.now()

        inner = func(context, config)

        runtime = datetime.now() - start_time

        result = Result(
            config,
            inner,
            None,
            start_time=start_time,
            runtime=runtime,
            cpu_time=None,
            memory=None,
            was_cached=True,
        )

    return inner


def _key(func: Callable, config: Config):
    # The default behaviour caches on all arguments, including the config object.
    return cloudpickle.dumps({"function": func, "args": [config]})
