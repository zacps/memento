import pytest
import os
import tempfile
import itertools

from simple_slurm import Slurm
from memento import Memento
from memento.slurm import backoff


@pytest.mark.slurm
class TestSlurm:
    def setup_method(self, method):
        # This is ugly, but sqlite3 doesn't seem to accept a file handle directly, so we need to
        # create a temporary file, close it (to not run afoul of locking on windows), then manually
        # remove it after we're done.
        # For HPC tests the database also needs to be on a path mapped into the containers, the current
        # directory is a convenient choice.
        file = tempfile.NamedTemporaryFile(
            suffix="_memento.cache", dir=".", delete=False
        )
        self._filepath = os.path.abspath(file.name)
        file.close()

    def teardown_method(self, method):
        os.unlink(self._filepath)

    def test_submit(self):
        def func(context, config):
            return config.k1

        memento = Memento(func)

        matrix = {
            "parameters": {"k1": ["v1", "v2", "v3"]},
            "runtime": {
                "cpus": 1,
                "mem_per_cpu": "80M",
                "output": f"/data/{Slurm.JOB_ID}_{Slurm.JOB_NAME}",
            },
        }

        results = memento.run(matrix, cache_path=self._filepath, slurm=True)

        assert [result.inner for result in results] == ["v1", "v2", "v3"]

    def test_cache(self):
        def func(context, config):
            return config.k1

        memento = Memento(func)

        matrix = {
            "parameters": {"k1": ["v1", "v2", "v3"]},
            "runtime": {
                "cpus": 1,
                "mem_per_cpu": "80M",
                "output": f"/data/{Slurm.JOB_ID}_{Slurm.JOB_NAME}",
            },
        }

        results = memento.run(matrix, cache_path=self._filepath, slurm=True)

        assert [result.inner for result in results] == ["v1", "v2", "v3"]
        assert not any([result.was_cached for result in results])

        results = memento.run(matrix, cache_path=self._filepath, slurm=True)

        assert [result.inner for result in results] == ["v1", "v2", "v3"]
        assert all([result.was_cached for result in results])

    def test_configuration_objects(self):
        def func(context, config):
            return config.k1

        memento = Memento(func)

        class MyObject:
            pass

        matrix = {
            "parameters": {"k1": [MyObject, {"dict": True}]},
            "runtime": {
                "cpus": 1,
                "mem_per_cpu": "80M",
                "output": f"/data/{Slurm.JOB_ID}_{Slurm.JOB_NAME}",
            },
        }

        results = memento.run(matrix, cache_path=self._filepath, slurm=True)

        assert [result.inner for result in results] == [
            MyObject,
            {"dict": True},
        ]


class TestBackoff:
    def test_backoff_intervals(self):
        assert list(itertools.islice(backoff(), 20)) == [
            1.0,
            1.3498588075760032,
            1.8221188003905089,
            2.4596031111569494,
            3.3201169227365472,
            4.4816890703380645,
            6.049647464412945,
            8.166169912567652,
            11.023176380641601,
            14.87973172487283,
            20.085536923187668,
            27.112638920657883,
            36.598234443677974,
            49.40244910553017,
            66.68633104092515,
            90.01713130052181,
            120.0,
            120.0,
            120.0,
            120.0,
        ]
