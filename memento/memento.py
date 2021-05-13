"""
Contains `Memento`, the main entry point of MEMENTO.
"""

import functools
import logging
import os
from datetime import datetime
from typing import Callable, List, Optional

import cloudpickle

from memento.parallel import TaskManager, delayed
from memento.caching import FileSystemCacheProvider, CacheProvider
from memento.configurations import configurations, Config
from memento.task_interface import Context, Result
from memento.exceptions import CacheMiss

logger = logging.getLogger(__name__)


class Memento:
    """
    The main class of MEMENTO. This is the 'front end' of MEMENTO with which you can run a
    configuration matrix and retrieve results from your experiments.
    """

    def __init__(self, func: Callable):
        """
        :param func: Your experiment code. This will be called with an experiment configuration.
        """
        self.func = func

    def run(  # pylint: disable=too-many-arguments
        self,
        matrix: dict,
        dry_run: bool = False,
        force_run: bool = False,
        force_cache: bool = False,
        cache_path: str = None,
    ) -> Optional[List[Result]]:
        """
        Run a configuration matrix and return it's results.

        :param matrix: A configuration matrix
        :param dry_run: Do not actually run experiments, just log what would be run
        :param force_run: Ignore the cache and re-run all experiments
        :param force_cache: Raise ``exceptions.CacheMiss`` if an experiment is not found in the
            cache
        :param cache_path: Path to save results. This defaults to the current working directory and
            can also be specified using ``MEMENTO_CACHE_PATH``.
        :returns: A list of results from your experiments.
        """

        configs = configurations(matrix)

        logger.info("Running configurations:")
        for config in configs:
            logger.info("  %s", config)

        if dry_run:
            logger.info("Exiting due to dry run")
            return None

        cache_provider = FileSystemCacheProvider(
            filepath=(
                cache_path
                or os.environ.get("MEMENTO_CACHE_PATH", None)
                or "memento.sqlite"
            ),
            key_provider=_key_provider,
        )
        manager = TaskManager()

        # Run tasks for which we have no cached result
        ran = []
        for config in configs:
            key = _key_provider(self.func, config)
            if not cache_provider.contains(key) or force_run:
                if force_cache:
                    raise CacheMiss(config)
                context = Context(key, cache_provider)
                manager.add_task(
                    delayed(_wrapper(self.func)(context, config, cache_provider))
                )
                ran.append(config)

        manager.run()

        results = [
            cache_provider.get(_key_provider(self.func, config)) for config in configs
        ]

        for result in results:
            if result.config in ran:
                result.was_cached = False

        logger.info(
            "%s/%s results retrieved from cache",
            len(configs) - len(ran),
            len(configs),
        )

        return results


def remove_checkpoints(cache_provider: CacheProvider, key: str):
    """
    Remove checkpoints in order to save space in database
    """
    if isinstance(cache_provider, FileSystemCacheProvider):
        with cache_provider as database:
            database.execute(f"DROP table {key}_checkpoint")


def _wrapper(func: Callable) -> Callable:
    """
    Wrapper which runs in the task thread. This is responsible for collecting performance metrics
    and writing to the cache.
    """

    @functools.wraps(func)
    def inner(
        context: Context, config: Config, cache_provider: CacheProvider
    ) -> Result:
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
        cache_provider.set(context.key, result)
        return result

    return inner


def _key_provider(func: Callable, config: Config):
    # The default behaviour caches on all arguments, including the config object.
    return cloudpickle.dumps({"function": func, "args": [config]})
