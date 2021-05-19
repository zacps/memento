import logging
import os
import tempfile

import pytest

from memento.memento import Memento


class TestMemento:
    def setup_method(self, method):
        # This is ugly, but sqlite3 doesn't seem to accept a file handle directly, so we need to
        # create a temporary file, close it (to not run afoul of locking on windows), then manually
        # remove it after we're done.
        file = tempfile.NamedTemporaryFile(suffix="_memento.cache", delete=False)
        self._filepath = os.path.abspath(file.name)
        file.close()

    def teardown_method(self, method):
        os.unlink(self._filepath)

    @pytest.mark.slow
    def test_memento(self):
        def func(context, config):
            return config.k1

        memento = Memento(func)
        matrix = {"parameters": {"k1": ["v1", "v2", "v3"]}}
        results = memento.run(matrix, cache_path=self._filepath)
        assert [result.inner for result in results] == ["v1", "v2", "v3"]

    def test_dry_run(self):
        def func(context, config):
            raise Exception("should not be called")

        memento = Memento(func)
        matrix = {"parameters": {"k1": ["v1", "v2", "v3"]}}
        results = memento.run(matrix, cache_path=self._filepath, dry_run=True)
        assert results is None

    @pytest.mark.slow
    def test_was_cached(self):
        def func(context, config):
            return config.k1

        memento = Memento(func)
        matrix = {"parameters": {"k1": ["v1", "v2"]}}
        results = memento.run(matrix, cache_path=self._filepath)
        matrix = {"parameters": {"k1": ["v1", "v2", "v3"]}}
        results = memento.run(matrix, cache_path=self._filepath)
        assert [result.inner for result in results] == ["v1", "v2", "v3"]
        assert [result.was_cached for result in results] == [True, True, False]

    @pytest.mark.slow
    def test_run_multiple(self):
        def func(context, config):
            return config.asdict()

        memento = Memento(func)

        memento.add_matrix({
            "id": 2,
            "dependencies": [1],
            "parameters": {
                "k1": ['a']
            }
        })

        memento.add_matrix({
            "id": 1,
            "dependencies": [],
            "parameters": {
                "k1": [1, 2, 3]
            }
        })

        results = memento.run_all(cache_path=self._filepath)
        assert all('1' in result.inner for result in results)
        assert [result.inner['1']['k1'] for result in results] == [1, 2, 3]
        assert [result.inner['k1'] for result in results] == ['a', 'a', 'a']

    @pytest.mark.slow
    def test_run_multiple_dry(self):
        def func(context, config):
            raise Exception("should not be called")

        memento = Memento(func)

        memento.add_matrix({
            "id": 2,
            "dependencies": [1],
            "parameters": {
                "k1": ['a']
            }
        })

        memento.add_matrix({
            "id": 1,
            "dependencies": [],
            "parameters": {
                "k1": [1, 2, 3]
            }
        })

        results = memento.run_all(cache_path=self._filepath, dry_run=True)
        assert results is None


