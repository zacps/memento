import pytest
from simple_slurm import Slurm
from memento import Memento


@pytest.mark.slurm
class TestSlurm:
    def test_submit_long(self):
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

        results = memento.run(matrix, slurm=True)

        assert [result.inner for result in results] == ["v1", "v2", "v3"]
