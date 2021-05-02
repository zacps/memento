from memento.metric import Metric, MetricDataPoint
import pandas as pd

from memento.parallel import TaskManager, delayed


class TestMetric:
    def test_metric_creates_singleton_instance(self):
        metric1 = Metric("name")
        metric2 = Metric("name")
        metric3 = Metric("not_name")

        assert metric1 is metric2
        assert metric1 is not metric3

    def test_metric_creates_singleton_instance_in_parallel(self):
        def task_1():
            metric1 = Metric("parallel")
            metric1.record(1.0, 1.0)
            metric1.record(2.0, 2.0)
            metric1.record(3.0, 3.0)

        def task_2():
            metric1 = Metric("parallel")
            metric1.record(4.0, 4.0)
            metric1.record(5.0, 5.0)
            metric1.record(6.0, 6.0)

        # Metric("parallel")  # Ensure that the metric exists beforehand
        manager = TaskManager(max_tasks_per_worker=1)
        manager.add_tasks([delayed(task_1)(), delayed(task_2)()])
        manager.run()

        expected_dataframe = pd.DataFrame([
            MetricDataPoint(1.0, 1.0),
            MetricDataPoint(2.0, 2.0),
            MetricDataPoint(3.0, 3.0),
            MetricDataPoint(4.0, 1.0),
            MetricDataPoint(5.0, 2.0),
            MetricDataPoint(6.0, 3.0),
        ])
        actual_dataframe = Metric("parallel").dump_to_df()

        assert expected_dataframe.equals(actual_dataframe)

    def test_metric_records_information_to_different_metrics(self):
        metric1 = Metric("test_metric_records_information_to_different_metrics_1")
        metric2 = Metric("test_metric_records_information_to_different_metrics_2")
        data1 = [
            MetricDataPoint(1.0, 1.0),
            MetricDataPoint(2.0, 2.0),
            MetricDataPoint(3.0, 3.0),
        ]
        data2 = [
            MetricDataPoint(4.0, 1.0),
            MetricDataPoint(5.0, 2.0),
            MetricDataPoint(6.0, 3.0),
        ]

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
