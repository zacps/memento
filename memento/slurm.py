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
import time
from uuid import uuid4
from itertools import chain
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile
from typing import Any, Callable, List

import cloudpickle
from simple_slurm import Slurm

from memento.configurations import Config


JOB_POLL_TIME = 10


def run_slurm(func: Callable, args_list: List[List[Any]], blocking=True):
    """
    Submit a list of jobs to slurm.
    """

    # pickle function and arguments to temp files
    files = (NamedTemporaryFile("wb", delete=False) for _ in args_list)

    ids = []
    for args, file in zip(args_list, files):
        config = args[1]
        internal_id = uuid4()
        cloudpickle.dump({"func": func, "args": args, "id": internal_id}, file)

        ids.append(_submit_job(file, config, internal_id))

    if blocking:
        __wait_jobs(ids)


def _submit_job(file, config: Config, internal_id: str):
    """
    Submit a single job to slurm.
    """
    slurm = Slurm(
        cpus_per_task=config.runtime["cpus"],
        mem_per_cpu=config.runtime["mem_per_cpu"],
        job_name=config.runtime.get("jobname", "memento"),
        comment=internal_id,
        output=config.runtime["output"],  # FIXME: Default to something sensible
    )
    # pass path to funcion and arguments
    slurm.sbatch(
        f"""
        {sys.executable} {__file__} {file.name}
        """
    )

    return internal_id


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


def __wait_jobs(ids):
    """
    Poll waiting for slurm jobs to complete. Because jobs timeout and are restarted the Slurm job
    IDs are not stable. Instead we make use of the job comment field (arbitrary text) to pass an
    internal ID. This internal ID is used to determine if a task has completed.
    """
    while True:
        out = subprocess.run(
            [
                "sacct",
                "-X",
                "-P",
                "-S",
                "now-48hour",
                "--format",
                "jobid,state,elapsed,start,comment%36",
            ],
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )
        jobs = csv.DictReader(out.stdout.splitlines(), delimiter="|")

        if all(job["STATE"] == "COMPLETED" for job in jobs):
            return

        seen_ids = {}
        for job in jobs[::-1]:
            # Jobs are returned in order from oldest start time first.
            # This stops us from considering earlier jobs for a particular task.
            if job["Comment"] in seen_ids:
                continue
            seen_ids.insert(job["Comment"])

            if job["STATE"] == "FAILED":
                # TODO: Give the node on which the job failed
                raise Exception(f"Job {job['JobID']} FAILED after {job['Elapsed']}")
            # State can be 'CANCELLED by ...'
            if "CANCELLED" in job["STATE"]:
                # TODO: Give the node on which the job failed
                raise Exception(
                    f"Job {job['JobID']} was CANCELLED after {job['Elapsed']}"
                )
            # TODO: This should be handled by the check script (expand memory allowance up to some maximum and resubmit)
            if "OUT_OF_MEMORY" in job["STATE"]:
                # TODO: Give the node on which the job failed
                raise Exception(
                    f"Job {job['JobID']} was CANCELLED after {job['Elapsed']}"
                )

        time.sleep(JOB_POLL_TIME)


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
        _submit_job(file, data["args"][1], data["id"])
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
