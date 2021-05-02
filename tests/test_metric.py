from memento.metric import Metric, MetricDataPoint
import pandas as pd


class TestMetric:
    def test_metric_creates_singleton_instance(self):
        metric1 = Metric("name")
        metric2 = Metric("name")
        metric3 = Metric("not_name")

        assert metric1 is metric2
        assert metric1 is not metric3

    def test_metric_creates_singleton_instance_in_parallel(self):
        metric1 = Metric()
        metric2 = Metric()

        assert True is False

    def test_metric_records_information_to_different_metrics(self):
        metric1 = Metric("test_metric_records_information_to_different_metrics_1")
        metric2 = Metric("test_metric_records_information_to_different_metrics_2")
        data1 = [MetricDataPoint("val1", 1.0),
                MetricDataPoint("val2", 2.0),
                MetricDataPoint("val3", 3.0)]
        data2 = [MetricDataPoint("val4", 1.0),
                 MetricDataPoint("val5", 2.0),
                 MetricDataPoint("val6", 3.0)]

        for datapoint in data1:
            metric1.record(datapoint.value, datapoint.time)
        for datapoint in data2:
            metric2.record(datapoint.value, datapoint.time)

        expected_df1 = pd.DataFrame(data1)
        expected_df2 = pd.DataFrame(data2)
        actual_df1 = metric1.dump_to_df()
        actual_df2 = metric2.dump_to_df()

        assert expected_df1.equals(actual_df1)
        assert expected_df2.equals(actual_df2)
        assert expected_df1.equals(expected_df2) is False

    def test_metric_records_mean_for_float_values(self):
        metric = Metric("test_metric_records_mean_for_float_values")
        metric.record(value=1.0)
        metric.record(value=2.0)

        assert metric.mean() == 1.5

    def test_metric_records_mean_for_int_values(self):
        metric = Metric("test_metric_records_mean_for_int_values")
        metric.record(value=1)
        metric.record(value=2)

        assert metric.mean() == 1.5

    def test_metric_records_median_for_odd_number_values(self):
        metric = Metric("test_metric_records_median_for_odd_number_values")
        metric.record(value=2.0)
        metric.record(value=1.0)
        metric.record(value=5.0)

        assert metric.median() == 2.0


    def test_metric_records_median_for_even_number_values(self):
        metric = Metric("test_metric_records_median_for_even_number_values")
        metric.record(value=2.0)
        metric.record(value=1.0)
        metric.record(value=5.0)
        metric.record(value=3.0)

        assert metric.median() == 2.5

    def test_metric_records_stdev(self):
        metric = Metric("test_metric_records_stdev")
        metric.record(value=1.0)
        metric.record(value=1.0)
        metric.record(value=1.0)

        assert metric.stdev() == 0.0

        metric.record(value=2.0)

        assert metric.stdev() == 0.5
