"""
Contains MEMENTO's task interface, once the configurations are
generated and dispatched to tasks, we need some way to interact
with the user code
"""
import datetime
import time
from collections import namedtuple
from typing import Any, Optional, Union, Tuple
import pandas as pd
from pandas import DataFrame
from memento.configurations import Config

Metric = namedtuple("Metric", 'x y')


class Context:
    """
    The ``Context`` makes MEMENTO's utilities like checkpointing, metrics,
    progress reporting, and more available to tasks.
    """
    _metrics: dict[str, list[Metric]]

    def __init__(self, key):
        """
        Each context is associated with exactly one task.
        """
        self.key = key
        self._metrics = {}

    def collect_metrics(self) -> dict[str, pd.DataFrame]:
        metrics: dict[str, DataFrame] = {}
        for name in self._metrics.keys():
            metrics[name] = pd.DataFrame(self._metrics[name])

        return metrics

    def record(self, metric_name: str = None, value: Union[float, Tuple[float, float]] = None,
               value_dict: dict[str, float] = None):
        supplied_no_values = (metric_name is None or value is None) and value_dict
        supplied_two_types_of_values = value is not None and value_dict is not None

        if supplied_no_values is None:
            raise ValueError("Must supply either name,value pair or a dictionary of name-value pairs.")
        if supplied_two_types_of_values:
            raise ValueError("Must supply only one of (name, value) or value_dict.")

        name_value_mapping: dict[str, float] = value_dict or {metric_name: value}
        x_value = time.time()

        for name in name_value_mapping.keys():
            y_value = name_value_mapping[name]

            # Handles the case of a tuple
            if isinstance(y_value, Tuple):
                x_value = y_value[0]
                y_value = y_value[1]

            metric = Metric(x_value, y_value)
            if self._metrics.get(name, False):
                self._metrics[name].append(metric)
            else:
                self._metrics[name] = [metric]

    def progress(self, delta, total=None):  # pylint: disable=no-self-use
        """
        Update the progress estimate, changing the current progress by ``delta``.

        The first call to this should (if possible) estimate the total amount of work.
        This can later be refined by passing a different value of ``total``.
        """
        raise NotADirectoryError("feature: progress")

    # Whether or not we checkpoint a particular value or not will depend on
    # if we implement full program checkpointing or not.
    def checkpoint(self, data: Any):
        """
        Save the current state of the task.
        """
        raise NotImplementedError("feature: checkpoints")

    def restore(self) -> Any:
        """
        Restore the state of the task from the last checkpoint.
        """
        raise NotImplementedError("feature: checkpoints")


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

    metrics: list[pd.DataFrame]

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
            metrics: list[pd.DataFrame],
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
