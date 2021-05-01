from dataclasses import dataclass
from time import time
import pandas as pd


@dataclass
class MetricDataPoint:
    def __init__(self, value, timestamp):
        self.value = value
        self.time = timestamp


class Metric(object):
    _data_points: list[MetricDataPoint]
    _instance = None

    # Creates a singleton, without having to call a .get_instance() method
    # Can just call obj = Metric() like normal, but will always create 1 instance
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Metric, cls).__new__(cls)
            cls._setup(cls._instance)
        return cls._instance

    def _setup(self):
        self._data_points = []

    def record(self, value, timestamp: time = None):
        timestamp = timestamp or time()
        data = MetricDataPoint(value, timestamp)
        self._data_points.append(data)

    def dump_to_df(self):
        return pd.DataFrame(self._data_points)
