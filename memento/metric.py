from dataclasses import dataclass
from time import time
import statistics
import pandas as pd


@dataclass
class MetricDataPoint:
    """
    An internal class for the Metric class, used to generate Pandas dataframes.
    Should NOT be called from user code.
    """
    time: time
    value: float

    def __init__(self, value: float, timestamp: time):
        """
        Create a MetricDataPoint. Should NOT be called from user code.
        :param value: The value to be recorded.
        :param timestamp: The timestamp of the value.
        """
        self.value = value
        self.time = timestamp


class Metric(object):
    """
    A class representing some metric within the program.

    To create a metric, do:
    ..
        my_metric = Metric("metric_name")

    To record a (float) value to a metric, do:
    ..
        my_metric.record(123.456)

    To get a Pandas dataframe of the metric, do:
    ..
        my_metric.dump_to_df()

    Calculated statistics of the metric are available, including:
    ..
        my_metric.mean()
        my_metric.median()
        my_metric.stdev()
    """
    _instances: dict
    _data_points: list[MetricDataPoint]

    # Creates a singleton, without having to call a .get_instance() method
    # Can just call obj = Metric("name") like normal, but will always create only 1 instance
    def __new__(cls, metric_name: str):
        """
        Creates a Metric object, which is a singleton.

        Metrics with the same name are the same object, and are created only once.

        ..
            metric1 = Metric("name1")
            metric2 = Metric("name2")
            metric3 = Metric("name1")

            metric1 is metric2 # False
            metric1 is metric3 # True

        :param metric_name: The name of the specific metric.
        :return: A Metric object.
        """
        try:
            return cls._instances[metric_name]
        # When the instances dict hasn't been instantiated
        except AttributeError:
            metric = super(Metric, cls).__new__(cls)
            cls._instances = {metric_name: metric}
            cls._setup(metric)
            return metric
        # When the specific metric name doesn't exist in the dict
        except KeyError:
            metric = super(Metric, cls).__new__(cls)
            cls._instances[metric_name] = metric
            cls._setup(metric)
            return metric

    def _setup(self) -> None:
        """
        The setup function for this class, replaces ``__init__()`` as that should not exist on a singleton.

        Run after the metric object is created.
        :return: None
        """
        self._data_points = []

    def _get_values(self) -> list[float]:
        """
        Returns all of the values recorded for this metric, without timestamps.
        :return: A list of all of the values recorded for this metric.
        """
        return [x.value for x in self._data_points]

    def record(self, value: float, timestamp: time = None) -> None:
        """
        Records a value to a specific metric, along with a timestamp.
        :param value: The (float) value to be recorded.
        :param timestamp: An optional timestamp value. Will be generated if not supplied.
        :return: None
        """
        timestamp = timestamp or time()
        data = MetricDataPoint(value, timestamp)
        self._data_points.append(data)

    def dump_to_df(self) -> pd.DataFrame:
        """
        Returns a Pandas dataframe containing the values and timestamps of the metric.
        :return: The Pandas dataframe of the metric's data.
        """
        return pd.DataFrame(self._data_points)

    def mean(self) -> float:
        """
        Calculates the mean of the metric's values.
        :return: The mean of the metric's values
        """
        return statistics.mean(self._get_values())

    def median(self) -> float:
        """
        Calculates the median of the metric's values.
        :return: The median of the metric's values
        """
        return statistics.median(self._get_values())

    def stdev(self) -> float:
        """
        Calculates the standard deviation of the metric's values.
        :return: The standard deviation of the metric's values
        """
        return statistics.stdev(self._get_values())
