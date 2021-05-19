"""
Contains `Memento`, the main entry point of MEMENTO.
"""

import functools
import logging
import os
from datetime import datetime
from typing import Callable, List, Optional
from networkx import DiGraph, is_directed_acyclic_graph, topological_sort

import cloudpickle

from memento.parallel import TaskManager, delayed
from memento.caching import FileSystemCacheProvider, CacheProvider
from memento.configurations import configurations, Config
from memento.task_interface import Context, Result
from memento.exceptions import CacheMiss, CyclicDependency

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
        self._matrices: List[dict] = []

    def add_matrix(self, matrix: dict):
        """
        Adds a configuration matrix.

        :param matrix: A configuration matrix
        """
        self._matrices.append(matrix)

    def run_all(self, **kwargs):
        """
        Runs this objects configuration matrices and returns it's results.

        :param kwargs: keyword arguments to Memento.run
        """

        # Construct graph representation of matrices

        graph_edges = []

        for matrix in self._matrices:
            for dependency in matrix["dependencies"]:
                graph_edges.append(tuple([matrix["id"], dependency]))

        graph = DiGraph()
        graph.add_edges_from(graph_edges)

        # Validate graph

        if not is_directed_acyclic_graph(graph):
            raise CyclicDependency()

        # Get execution order via a topological sort

        matrices = topological_sort(graph)

        n_matrices = len(matrices)

        # Run each matrix
        for i in range(n_matrices):
            matrix = matrices[i]
            results = self.run(matrix, **kwargs)

            # If this is the last matrix, just return it's results
            if i == n_matrices - 1:
                return results

            inners = [result.inner for result in results]

            # Update all matrices that depend on the matrix that was just run
            for mat in matrices[i+1:]:
                if matrix['id'] in mat['dependencies']:
                    mat['dependencies'][matrix['id']] = inners

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

        cache = FileSystemCacheProvider(
            filepath=(
                    cache_path
                    or os.environ.get("MEMENTO_CACHE_PATH", None)
                    or "memento.sqlite"
            ),
            key=_key,
        )
        manager = TaskManager()

        # Run tasks for which we have no cached result
        ran = []
        for config in configs:
            key = _key(self.func, config)
            if not cache.contains(key) or force_run:
                if force_cache:
                    raise CacheMiss(config)
                context = Context(key)
                manager.add_task(delayed(_wrapper(self.func)(context, config, cache)))
                ran.append(config)

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
    Wrapper which runs in the task thread. This is responsible for collecting performance metrics
    and writing to the cache.
    """

    @functools.wraps(func)
    def inner(context: Context, config: Config, cache: CacheProvider) -> Result:
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
        cache.set(context.key, result)

        return result

    return inner


def _key(func: Callable, config: Config):
    # The default behaviour caches on all arguments, including the config object.
    return cloudpickle.dumps({"function": func, "args": [config]})
