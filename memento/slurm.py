"""
Integration with the Slurm HPC workload manager.

Each task consists of two jobs. The main job starts by submitting a check job, then enters user code.
The check job has a dependency on the main job, and restarts it if necessary. It is also in charge of
notifying errors such as OOM that could not be caught by the main job.

The high level picture can be seen in the diagram below:

.. graphviz:: slurm.dot

Each grey box is a slurm job. The main slurm job is submitted by ``submit_main`` and goes on to trigger
a check job, which in turn triggers the next main job.
"""

import sys
import subprocess
import csv
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile
from typing import Any, Callable, List

import cloudpickle
from simple_slurm import Slurm

from memento.configurations import Config


def run_slurm(func: Callable, args_list: List[List[Any]]):
    """
    Submit a list of jobs to slurm.
    """

    # pickle function and arguments to temp files
    files = (NamedTemporaryFile("w", delete=False) for _ in args_list)

    for args, file in zip(args_list, files):
        config = args[1]
        cloudpickle.dump({"func": func, "args": args}, file)

        _submit_job(file, config)


def _submit_job(file, config):
    """
    Submit a single job to slurm.
    """
    slurm = Slurm(
        cpus_per_task=config.runtime.cpus,
        mem_per_cpu=config.runtime.mem_per_cpu,
        job_name=config.runtime.job_name or f"memento",  # FIXME: More useful job name
        output=config.runtime.output,  # FIXME: Default to something sensible
    )
    # pass path to funcion and arguments
    slurm.sbatch(
        f"""
        {sys.executable} {__file__} {file.name}
        """
    )


def _submit_check(filename: str, config: Config):
    """
    Submit a check job to slurm.
    """
    slurm = Slurm(
        cpus_per_task=1,
        mem_per_cpu="50M",
        job_name=f"{config.runtime.job_name}-check" or f"memento-check",
        dependency={"after": sys.environ["SLURM_JOB_ID"]},
        output="",
        time="0-00:01:00",
    )
    # pass path to funcion and arguments
    slurm.sbatch(
        f"""
        {sys.executable} {__file__} {filename} --check={sys.environ["SLURM_JOB_ID"]}
        """
    )


def _run_check(file, data, job_id):
    """
    Check the exit status of the main job. Restart it if it timed out.
    """
    out = subprocess.run(
        ["sacct", "-X", "-j", job_id, "-P"],
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )
    jobs = csv.DictReader(out.stdout.splitlines(), delimiter="|")
    state = next(jobs)["State"]

    if state == "COMPLETED":
        # We're done
        pass
    elif state == "TIMEOUT":
        _submit_job(file, data["args"][1])
    else:
        # An unexpected error occured
        pass


def _run_job(data):
    """
    Run the actual job.
    """
    data["func"](*data["args"])


def _entrypoint():
    """
    Entrypoint for both check and main jobs.
    """
    parser = ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--check")

    args = parser.parse_args()

    # load function and arguments
    with open(args.file, "wb") as f:
        data = cloudpickle.load(f)

    if args.check:
        _run_check(args.file, data, args.check)
    else:
        _submit_check(args.file, data["args"][1])
        _run_job(data)


if __name__ == "__main__":
    _entrypoint()
