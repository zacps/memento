"""
Contains classes and functions for running tasks in parallel.
"""
import sys
from contextlib import redirect_stdout, redirect_stderr, contextmanager
from multiprocessing.pool import Pool
from typing import Callable, List, TextIO, Iterable

import dill


def delayed(func: Callable):
    """
    Creates a version of the given function that stores the arguments of it's first call.

    ### Example:

    ```python
    delayed(sum)([1, 2])() # Equivalent to calling sum([1, 2])
    ```
    """

    def args_wrapper(*args, **kwargs):
        def wrapped():
            return func(*args, **kwargs)

        return wrapped

    return args_wrapper


@contextmanager
def _redirect_stdio(prefix: str):
    """
    Redirects stdout and stderr to a stream that adds the given prefix to any text that is output.
    """
    with redirect_stdout(_PrefixedStream(sys.stdout, prefix)):
        with redirect_stderr(_PrefixedStream(sys.stderr, prefix)):
            yield


class _PrefixedStream:
    def __init__(self, stream: TextIO, prefix: str):
        self._stream = stream
        self._prefix = prefix

    def write(self, text: str):
        """ Writes the given text with a prefix. """
        text = text.rstrip()
        if text:
            self._stream.write(f'{self._prefix}{text}\n')

    def flush(self):
        """ Flushes the stream. """
        self._stream.flush()


class _Task:
    def __init__(self, identifier: str, task: Callable):
        self._identifier = identifier
        self._task = dill.dumps(task)

    @property
    def identifier(self):
        """ Returns this job's identifier. """
        return self._identifier

    def run(self):
        """ Runs this task and returns it's result. """
        return dill.loads(self._task)()


def _worker(task: '_Task'):
    """ Initializer function for pool.map. """
    with _redirect_stdio(f'{task.identifier}: '):
        return task.run()


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

    def __init__(self, workers: int = None, max_tasks_per_worker: int = None):
        self._workers = workers
        self._max_tasks_per_worker = max_tasks_per_worker
        self._id_count: int = 0
        self._tasks: List[_Task] = []

    def _create_task(self, callable_: Callable) -> _Task:
        self._id_count += 1
        return _Task(f'Task {self._id_count}', callable_)

    def add_task(self, callable_: Callable):
        """ Adds the given task to the end of this task manager's queue. """

        if not callable(callable_):
            raise TypeError(f"'callable' must of type 'Callable' but was '{type(callable_)}'")

        task = self._create_task(callable_)
        self._tasks.append(task)

    def add_tasks(self, callables: Iterable[Callable]):
        """ Adds the given tasks to the end of this task manager's queue. """
        for callable_ in callables:
            self.add_task(callable_)

    def run(self):
        """ Runs this task manager's tasks and returns the results. """
        with Pool(processes=self._workers, maxtasksperchild=self._max_tasks_per_worker) as pool:
            results = pool.map(_worker, self._tasks)
        self._tasks.clear()
        return results
