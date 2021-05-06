"""
Contains MEMENTO's task interface, once the configurations are
generated and dispatched to tasks, we need some way to interact
with the user code
"""
from typing import Any, Callable, Optional
import datetime
from memento.caching import CacheProvider, Cache
from memento.configurations import Config


class Context:
    """
    The ``Context`` makes MEMENTO's utilities like checkpointing, metrics,
    progress reporting, and more available to tasks.
    """

    def __init__(self, key, cache_provider: CacheProvider):
        """
        Each context is associated with exactly one task.
        """
        self.key = key
        self._cache_provider = cache_provider

    def collect_metrics(self, *metrics: Callable):
        """
        Gets the new metrics to start next experiment
        """
        raise NotImplementedError("feature: metrics")

    def progress(self, delta, total=None):  # pylint: disable=no-self-use
        """
        Update the progress estimate, changing the current progress by ``delta``.
        The first call to this should (if possible) estimate the total amount of work.
        This can later be refined by passing a different value of ``total``.
        """
        raise NotADirectoryError("feature: progress")

    # Whether or not we checkpoint a particular value or not will depend on
    # if we implement full program checkpointing or not.
    def checkpoint(self, func: callable):
        """
        Save the current state of the task.
        """
        return Cache(func, self._cache_provider)


class MemoryUsage:
    """
    Memory usage statistics recorded from a task.
    """

    virtual_peak: int
    hardware_peak: int

    def __init__(self, virtual_peak: int, hardware_peak: int):
        self.virtual_peak = virtual_peak
        self.hardware_peak = hardware_peak


class Result:
    """
    The result from a single task. This contains the value returned from the experiment, ``inner``,
    and metadata about the task run.
    """

    config: Config

    inner: Any

    metrics: Any

    "The start time of the task."
    start_time: datetime.datetime

    "The task's runtime, measured on the wall clock."
    runtime: datetime.timedelta
    "The task's runtime, measured by the CPU"
    cpu_time: Optional[datetime.timedelta]
    "Memory usage statistics"
    memory: Optional[MemoryUsage]

    "Whether or not this result was retrieved from cache."
    was_cached: bool

    def __init__(  # pylint: disable=too-many-arguments
            self,
            config,
            inner,
            metrics,
            start_time: datetime.datetime,
            runtime: datetime.timedelta,
            cpu_time: Optional[datetime.timedelta],
            memory: Optional[MemoryUsage],
            was_cached: bool,
    ):
        self.config = config
        self.inner = inner
        self.metrics = metrics
        self.start_time = start_time
        self.runtime = runtime
        self.cpu_time = cpu_time
        self.memory = memory
        self.was_cached = was_cached
