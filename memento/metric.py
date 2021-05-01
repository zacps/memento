from dataclasses import dataclass
from time import time
from typing import Any, Union

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

    def record(self, value: float, timestamp: time = None):
        timestamp = timestamp or time()
        data = MetricDataPoint(value, timestamp)
        self._data_points.append(data)

    def dump_to_df(self):
        return pd.DataFrame(self._data_points)

    def mean(self):
        return sum([x.value for x in self._data_points]) / len(self._data_points)
