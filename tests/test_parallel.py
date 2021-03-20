"""
Contains tests for parallel.py.
"""

import functools
import multiprocessing
from typing import List, Callable

import pytest

from memento.parallel import TaskManager, delayed


def get_process_id():
    return id(multiprocessing.current_process())


def test_parallel_uses_multiple_processes():
    """ Multiple processes are used when running tasks. """
    manager = TaskManager(max_tasks_per_worker=1)
    manager.add_tasks((delayed(get_process_id)() for _ in range(10)))
    results = manager.run()

    assert len(set(results)) > 1


def test_parallel_uses_correct_number_of_processes():
    """ Multiple processes are used up to the specified limit when possible. """
    manager = TaskManager(max_tasks_per_worker=2, workers=5)
    manager.add_tasks((delayed(get_process_id)() for _ in range(10)))
    results = manager.run()

    assert len(set(results)) <= 5


class TestClass:
    def __init__(self, x: int, y: int):
        self._result = x + y

    def __eq__(self, other):
        return isinstance(other, TestClass) and self._result == other._result


class CallableTestClass:
    def __call__(self, x: int, y: int):
        return x + y


def recursive_function(x: int):
    if x <= 0:
        return 0
    return 1 + recursive_function(x - 1)


@pytest.mark.parametrize(
    "task,expected",
    [
        (delayed(sum)([1, 2]), [3]),
        (delayed(lambda x: sum(x))([2, 2]), [4]),
        (delayed(functools.partial(lambda x, y: sum([x, y]), 2))(3), [5]),
        (delayed(TestClass)(3, 3), [TestClass(3, 3)]),
        (delayed(CallableTestClass())(3, 4), [7]),
        (delayed(recursive_function)(8), [8]),
    ],
)
def test_parallel_returns_correct_result(task: Callable, expected: List):
    """ The correct result is returned when tasks are run. """
    manager = TaskManager()
    manager.add_task(task)
    results = manager.run()

    assert results == expected
