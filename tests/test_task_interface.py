from memento.task_interface import Context


class TestContext:
    class TestRecord:
        def test_record_records_single_value(self):
            context = Context("key")
            context.record("name", 1)
            context.record("name", 2)

            metrics = context.collect_metrics()

            assert metrics.__contains__("name")

            expected_y_values = [1.0, 2.0]
            actual_y_values = list(metrics["name"]["y"])

            assert expected_y_values == actual_y_values

        def test_record_records_multiple_values_at_same_timestamp(self):
            context = Context("key")
            context.record(value_dict={"name1": 1.0, "name2": 2.0})

            metrics = context.collect_metrics()

            assert metrics.__contains__("name1")
            assert metrics.__contains__("name2")

            expected_y_values_1 = [1.0]
            actual_y_values_1 = list(metrics["name1"]["y"])
            expected_y_values_2 = [2.0]
            actual_y_values_2 = list(metrics["name2"]["y"])
            x_values_1 = list(metrics["name1"]["x"])
            x_values_2 = list(metrics["name2"]["x"])

            assert expected_y_values_1 == actual_y_values_1
            assert expected_y_values_2 == actual_y_values_2
            assert x_values_1 == x_values_2
