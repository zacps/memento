"""
Contains MEMENTO's task interface, once the configurations are
generated and dispatched to tasks, we need some way to interact
with the user code
"""
import datetime
import time
from collections import namedtuple
from typing import Any, Optional, Union, Tuple, Dict, List, cast
import pandas as pd
from pandas import DataFrame
from memento.configurations import Config

Metric = namedtuple("Metric", "x y")


class Context:
    """
    The ``Context`` makes MEMENTO's utilities like checkpointing, metrics,
    progress reporting, and more available to tasks.
    """

    _metrics: Dict[str, List[Metric]]

    def __init__(self, key):
        """
        Each context is associated with exactly one task.
        """
        self.key = key
        self._metrics = {}

    def collect_metrics(self) -> Dict[str, pd.DataFrame]:
        """
        Collects all of the metrics as dataframes.
        :return: A dictionary of metric names that map to Pandas Dataframes.
        """
        metrics: Dict[str, DataFrame] = {}
        for name in self._metrics:
            metrics[name] = pd.DataFrame(self._metrics[name])

        return metrics

    def record(self, value_dict: Dict[str, Union[float, Tuple[float, float]]]) -> None:
        """
        Records a floating point metric in one of the following formats.
        Default x value is a timestamp.
        Metrics are available as part of the results object.

        ..
            context.record({"metric_name": value})
            context.record({"metric_name": (x,y)})

            # Record with the same timestamp
            context.record({"metric_1": value1, "metric_2": value2})

        :return: None.
        :param value_dict:
        """
        x_value = time.time()

        for name in value_dict:
            y_value = value_dict[name]

            # Handles the case of a tuple
            if type(y_value) is tuple:
                y_value = cast(Tuple[float, float], y_value)
                x_value = y_value[0]
                y_value = y_value[1]

            # Type guards that shouldn't be triggered.
            assert type(x_value) is float
            assert type(y_value) is float

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

    metrics: Dict[str, pd.DataFrame]

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
        metrics: Dict[str, pd.DataFrame],
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
