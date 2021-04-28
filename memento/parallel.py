"""
Contains classes and functions for running tasks in parallel.
"""
import sys
from contextlib import redirect_stdout, redirect_stderr, contextmanager
from functools import wraps
from heapq import heapify
from multiprocessing.pool import Pool
from .notifications import DefaultNotificationProvider, NotificationProvider
from typing import Callable, List, TextIO, Iterable

import cloudpickle


def delayed(func: Callable):
    """
    Creates a version of the given function that stores the arguments of it's first call.

    ### Example:

    ```python
    delayed(sum)([1, 2])() # Equivalent to calling sum([1, 2])
    ```
    """

    def args_wrapper(*args, **kwargs):
        @wraps(func)
        def wrapped():
            return func(*args, **kwargs)

        return wrapped

    return args_wrapper


@contextmanager
def _redirect_stdio(prefix: str):
    """
    Redirects stdout and stderr to a stream that adds the given prefix to any text that is output.
    """
    # TODO: `_PrefixedStream` does not satisfy the `_T_io` type parameter for `redirect_std*``
    with redirect_stdout(_PrefixedStream(sys.stdout, prefix)):  # type: ignore
        with redirect_stderr(_PrefixedStream(sys.stderr, prefix)):  # type: ignore
            yield


class _PrefixedStream:
    def __init__(self, stream: TextIO, prefix: str):
        self._stream = stream
        self._prefix = prefix

    def write(self, text: str):
        """ Writes the given text with a prefix. """
        text = text.rstrip()
        if text:
            self._stream.write(f"{self._prefix}{text}\n")

    def flush(self):
        """ Flushes the stream. """
        self._stream.flush()


class _Task:
    def __init__(self, identifier: str, index: int, task: Callable, priority: int,
                 notification_provider: NotificationProvider):
        self._identifier = identifier
        self._task = cloudpickle.dumps(task)
        self._priority = priority
        self._index = index
        self._notification_provider = cloudpickle.dumps(notification_provider)

    @property
    def identifier(self):
        """ Returns this job's identifier. """
        return self._identifier

    @property
    def index(self):
        """ Returns this job's index. """
        return self._index

    def run(self):
        """ Runs this task and returns it's result. """
        notification_provider = cloudpickle.loads(self._notification_provider)

        try:
            task_return = cloudpickle.loads(self._task)()
            notification_provider.task_completion()
            return task_return
        except Exception as e:
            notification_provider.task_failure()
            raise e

    def __lt__(self, other: "_Task"):
        """ Compares the priority between two tasks """
        return self._priority < other._priority


def _worker(task: "_Task"):
    """ Initializer function for pool.map. """
    with _redirect_stdio(f"{task.identifier}: "):
        return task.index, task.run()


TASK_PRIORITY_LOW: int = 3
TASK_PRIORITY_MEDIUM: int = 2
TASK_PRIORITY_HIGH: int = 1


class TaskManager:
    """
    Provides a simple interface for running multiple tasks in parallel.

    ### Examples

    ```python
    manager = TaskManager()
    manager.add_task(delayed(lambda x: print(x))("Hello World!"))
    manager.run()
    ```

    ```python
    manager.add_task(delayed(sum)([1, 2]))
    results = manager.run()
    print(results)
    ```

    """

    def __init__(self, workers: int = None, max_tasks_per_worker: int = None,
                 notification_provider: NotificationProvider = DefaultNotificationProvider):
        self._workers = workers
        self._max_tasks_per_worker = max_tasks_per_worker
        self._id_count: int = 0
        self._tasks: List[_Task] = []
        self._task_index = 0
        self._notification_provider = notification_provider

    def _create_task(self, callable_: Callable, priority_: int) -> _Task:
        self._id_count += 1
        task = _Task(f"Task {self._id_count}", self._task_index, callable_, priority_, self._notification_provider)
        self._task_index += 1
        return task

    def add_task(self, callable_: Callable, priority: int = TASK_PRIORITY_HIGH):
        """ Adds the given task to the end of this task manager's queue. """

        if not callable(callable_):
            raise TypeError(
                f"'callable' must of type 'Callable' but was '{type(callable_)}'"
            )

        if priority < 0:
            raise ValueError(f"'priority' must be positive but was '{priority}'")

        task = self._create_task(callable_, priority)
        self._tasks.append(task)

    def add_tasks(
            self, callables: Iterable[Callable], priority: int = TASK_PRIORITY_HIGH
    ):
        """ Adds the given tasks to the end of this task manager's queue. """
        for callable_ in callables:
            self.add_task(callable_, priority)

    def run(self):
        """ Runs this task manager's tasks and returns the results. """
        heapify(self._tasks)
        with Pool(
                processes=self._workers, maxtasksperchild=self._max_tasks_per_worker
        ) as pool:
            results = pool.map(_worker, self._tasks)
        self._tasks.clear()

        # At this point results is a list of tuples -> (task_index, task_result) so we can sort

        results.sort(key=lambda t: t[0])
        results = [item[1] for item in results]

        self._notification_provider.job_completion()

        return results
