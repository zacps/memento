from memento.memento import Memento


class TestMemento:
    def test_memento(self):
        def func(context, config):
            return config.k1

        memento = Memento(func)
        matrix = {"parameters": {"k1": ["v1", "v2", "v3"]}}
        results = memento.run(matrix)
        assert [result.inner for result in results] == ["v1", "v2", "v3"]

    def test_dry_run(self):
        def func(context, config):
            raise Exception("should not be called")

        memento = Memento(func)
        matrix = {"parameters": {"k1": ["v1", "v2", "v3"]}}
        results = memento.run(matrix, dry_run=True)
        assert results is None
