from memento.metric import Metric, MetricDataPoint
import pandas as pd


class TestMetric:
    def test_metric_creates_singleton_instance(self):
        metric1 = Metric()
        metric2 = Metric()

        assert metric1 is metric2

    def test_metric_creates_singleton_instance_in_parallel(self):
        metric1 = Metric()
        metric2 = Metric()

        assert True is False

    def test_metric_records_information_and_dumps_to_df(self):
        metric = Metric()
        data = [MetricDataPoint("val1", 1.0),
                MetricDataPoint("val2", 2.0),
                MetricDataPoint("val3", 3.0)]

        for datapoint in data:
            metric.record(datapoint.value, datapoint.time)

        expected_df = pd.DataFrame(data)
        actual_df = metric.dump_to_df()

        assert expected_df.equals(actual_df)