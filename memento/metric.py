from dataclasses import dataclass
from time import time
import statistics

import pandas as pd


@dataclass
class MetricDataPoint:
    time: time
    value: float

    def __init__(self, value: float, timestamp: time):
        self.value = value
        self.time = timestamp


class Metric(object):
    _data_points: list[MetricDataPoint]

    def __init__(self):
        self._data_points = []

    def _get_values(self) -> list[float]:
        return [x.value for x in self._data_points]

    def record(self, value: float, timestamp: time = None):
        timestamp = timestamp or time()
        data = MetricDataPoint(value, timestamp)
        self._data_points.append(data)

    def dump_to_df(self):
        return pd.DataFrame(self._data_points)

    def mean(self) -> float:
        return statistics.mean(self._get_values())

    def median(self) -> float:
        return statistics.median(self._get_values())

    def stdev(self) -> float:
        return statistics.stdev(self._get_values())
