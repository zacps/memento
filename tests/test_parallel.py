"""
Contains tests for parallel.py.
"""

import functools
import os
from typing import List, Callable

import pytest

from memento.parallel import TaskManager, delayed


def test_parallel_uses_multiple_processes():
    """ Multiple processes are used when running tasks. """
    manager = TaskManager(max_tasks_per_worker=1)
    manager.add_tasks((delayed(os.getpid)() for _ in range(10)))
    results = manager.run()

    assert len(set(results)) == len(results)


def test_parallel_uses_correct_number_of_processes():
    """ Multiple processes are used up to the specified limit when possible. """
    manager = TaskManager(max_tasks_per_worker=2, workers=5)
    manager.add_tasks((delayed(os.getpid)() for _ in range(10)))
    results = manager.run()

    assert len(set(results)) == 5


@pytest.mark.parametrize("task,expected", [
    (delayed(sum)([1, 2]), [3]),
    (delayed(lambda x: sum(x))([2, 2]), [4]),
    (delayed(functools.partial(lambda x, y: sum([x, y]), 2))(3), [5]),
])
def test_parallel_returns_correct_result(task: Callable, expected: List):
    """ The correct result is returned when tasks are run. """
    manager = TaskManager()
    manager.add_task(task)
    results = manager.run()

    assert results == expected
