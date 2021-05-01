from memento.metric import Metric


class TestMetric:
    def test_metric_creates_singleton_instance(self):
        metric1 = Metric()
        metric2 = Metric()

        assert metric1 is metric2

    def test_metric_creates_singleton_instance_in_parallel(self):
        metric1 = Metric()
        metric2 = Metric()

        assert True is False
