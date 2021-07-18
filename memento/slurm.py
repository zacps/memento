"""
Integration with the Slurm HPC workload manager.

Each task consists of two jobs. The main job starts by submitting a check job, then enters user
code. The check job has a dependency on the main job, and restarts it if necessary. It is also in
charge of notifying errors such as OOM that could not be caught by the main job.

The high level picture can be seen in the diagram below:

.. graphviz:: slurm.dot

Each grey box is a slurm job. The main slurm job is submitted by ``submit_main`` and goes on to
trigger a check job, which in turn triggers the next main job.

Currently this implementation makes the following assumptions (and will catch fire if they are not
met):
* There is a shared filesystem at /data (FIXME: Make configurable) with read/write permissions (on
  login and all worker nodes)
* The current python executable is also available at the same path (and is the same version) on
  worker nodes.
"""

import logging
import sys
import os
import subprocess
import csv
import time
import math
from uuid import uuid4
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile
from typing import Any, Callable, List

import cloudpickle
from simple_slurm import Slurm

from memento.configurations import Config


logger = logging.getLogger(__name__)


def run_slurm(func: Callable, args_list: List[List[Any]], blocking=True):
    """
    Submit a list of jobs to slurm.
    """

    # pickle function and arguments to temp files
    # FIXME: This needs to be configurable to a directory shared between the login and
    # compute nodes. It is used to transfer the argument data to the job.
    # Ideally we'd autodetect the shared filesystem, but I'm not sure that's easy/possible?
    files = (NamedTemporaryFile("wb", delete=False, dir="/data") for _ in args_list)

    ids = []
    for args, file in zip(args_list, files):
        config = args[1]
        internal_id = uuid4()
        cloudpickle.dump({"func": func, "args": args, "id": internal_id}, file)
        # Required so changes are persisted before the inner jobs start. Otherwise
        # they may only observe partial writes and fail to start.
        file.flush()

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
        # TODO: Ideally we should be able to identify the output file for each job,
        # then we can do things like attach the output to exceptions or error messages.
        output=config.runtime["output"],  # FIXME: Default to something sensible
    )
    # pass path to funcion and arguments
    command = f"PYTHONPATH={':'.join(sys.path)} {sys.executable} {__file__} {file.name}"
    logger.debug("Scheduling job with command %s", command)
    slurm.sbatch(command)

    return internal_id


def _submit_check(filename: str, config: Config):
    """
    Submit a check job to slurm.
    """
    slurm = Slurm(
        cpus_per_task=1,
        mem_per_cpu="50M",
        job_name=f"{config.runtime.get('jobname', 'memento')}-check" or "memento-check",
        dependency={"after": os.environ["SLURM_JOB_ID"]},
        # output="",
        time="0-00:01:00",
    )
    logger.debug("Check job batch script:\n%s", str(slurm))
    # pass path to funcion and arguments
    slurm.sbatch(
        f"""
        PYTHONPATH={":".join(sys.path)} {sys.executable} {__file__} {filename} --check={os.environ["SLURM_JOB_ID"]}
        """,
    )


def __wait_jobs(ids):
    """
    Poll waiting for slurm jobs to complete. Because jobs timeout and are restarted the Slurm job
    IDs are not stable. Instead we make use of the job comment field (arbitrary text) to pass an
    internal ID. This internal ID is used to determine if a task has completed.
    """
    poll_time = backoff()
    ids = [str(_id) for _id in ids]
    while True:
        logger.debug("Checking job IDs %s", ids)
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
            stderr=subprocess.PIPE,
            encoding="utf-8",
            check=True,
        )
        assert (
            out.returncode == 0
        ), f"FAILED to check job status with sacct: '{out.stderr}'"
        jobs = list(csv.DictReader(out.stdout.splitlines(), delimiter="|"))

        jobs = [job for job in jobs if job["Comment"].strip() in ids]

        states = {}
        for id in ids:
            for job in jobs:
                if job["Comment"].strip() == id:
                    states[id] = job["State"]
                    break
            else:
                states[id] = "MEMENTO_NO_SLURM_JOB_FOUND"

        logger.debug("\n".join([f"'{id}': {state}" for id, state in states.items()]))

        if all(state == "COMPLETED" for state in states.values()):
            logger.debug("All jobs completed")
            return

        seen_ids = set()
        for job in jobs[::-1]:
            # Jobs are returned in order from oldest start time first.
            # This stops us from considering earlier jobs for a particular task.
            if job["Comment"] in seen_ids:
                continue
            seen_ids.add(job["Comment"])

            if job["State"] == "FAILED":
                # TODO: Give the node on which the job failed
                raise Exception(f"Job {job['JobID']} FAILED after {job['Elapsed']}")
            # State can be 'CANCELLED by ...'
            if "CANCELLED" in job["State"]:
                # TODO: Give the node on which the job failed
                raise Exception(
                    f"Job {job['JobID']} was CANCELLED after {job['Elapsed']}"
                )
            # TODO: This should be handled by the check script (expand memory allowance up to some
            # maximum and resubmit)
            if "OUT_OF_MEMORY" in job["State"]:
                # TODO: Give the node on which the job failed
                raise Exception(
                    f"Job {job['JobID']} was CANCELLED after {job['Elapsed']}"
                )

        time.sleep(next(poll_time))


def _run_check(file, data, job_id):
    """
    Check the exit status of the main job. Restart it if it timed out.
    """
    out = subprocess.run(
        ["sacct", "-X", "-j", job_id, "-P"],
        stdout=subprocess.PIPE,
        encoding="utf-8",
        check=True,
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
    with open(args.file, "rb") as f:
        data = cloudpickle.load(f)
    os.unlink(args.file)

    if args.check:
        _run_check(args.file, data, args.check)
    else:
        _submit_check(args.file, data["args"][1])
        _run_job(data)


def backoff(start=1.0, stop=120.0, A=0.3):
    """
    Backoff for slurm polling.
    """
    i = 0
    while True:
        yield min(start * math.exp(i * A), stop)
        i += 1


if __name__ == "__main__":
    _entrypoint()
