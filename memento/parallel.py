"""
Contains classes and functions for running tasks in parallel.
"""
import sys
from ctypes import c_bool
from multiprocessing import Process, Queue, cpu_count, current_process, Value
from contextlib import redirect_stdout, redirect_stderr, contextmanager
from functools import wraps
from queue import Empty
from typing import Callable, List, TextIO, Iterable, Tuple, Dict

import dill


_SENTINEL = "STOP"


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
            self._stream.write(f"{self._prefix}{text}\n")

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


def _task_runner(task: _Task):
    """ Worker function for _Pool.map used by TaskManager. """
    with _redirect_stdio(f"{task.identifier}: "):
        result = task.run()
        return result


def _worker(tasks: Queue, results: Queue, worker_queue: Queue, max_tasks: int):
    """ Initializer for _Pool worker processes. """
    tasks_complete = 0
    for func, arg in iter(tasks.get, _SENTINEL):
        results.put(func(arg))

        tasks_complete += 1
        if max_tasks > 0 and tasks_complete >= max_tasks:
            worker_queue.put(current_process().pid)
            break


def _process_manager(
    tasks: Queue,
    results: Queue,
    exit_flag: Value,
    workers: int = None,
    max_tasks_per_worker: int = None,
):
    """ Initializer for ProcessManager. """
    _Pool.ProcessManager(tasks, results, exit_flag, workers, max_tasks_per_worker)


class _Pool:
    class ProcessManager:
        def __init__(
            self,
            tasks: Queue,
            results: Queue,
            exit_flag: Value,
            workers: int = None,
            max_tasks_per_worker: int = None,
        ):
            self._workers = workers or cpu_count()
            self._max_tasks_per_worker = max_tasks_per_worker or 0
            self._worker_queue = Queue()
            self._exit_flag = exit_flag
            self._worker_processes: Dict[int, Process] = dict()
            self._tasks = tasks
            self._results = results
            self._start_workers()
            self._run()

        def _start_workers(self):
            processes = [
                Process(
                    target=_worker,
                    args=(
                        self._tasks,
                        self._results,
                        self._worker_queue,
                        self._max_tasks_per_worker,
                    ),
                )
                for _ in range(self._workers)
            ]

            for process in processes:
                process.start()
                self._worker_processes[process.pid] = process

        def _run(self):
            # TODO: remove busy loop
            while not self._exit_flag.value:
                try:
                    pid = self._worker_queue.get_nowait()
                except Empty:
                    continue

                del self._worker_processes[pid]

                process = Process(
                    target=_worker,
                    args=(
                        self._tasks,
                        self._results,
                        self._worker_queue,
                        self._max_tasks_per_worker,
                    ),
                )
                process.start()
                self._worker_processes[process.pid] = process

            self._exit()

        def _exit(self):
            for _ in range(self._workers):
                self._tasks.put(_SENTINEL)

            for process in self._worker_processes.values():
                process.join()

    def __init__(self, workers: int = None, max_tasks_per_worker: int = None):
        self._tasks = Queue()
        self._results = Queue()
        self._exit_flag = Value(c_bool, False)
        self._process_manager = Process(
            target=_process_manager,
            args=(
                self._tasks,
                self._results,
                self._exit_flag,
                workers,
                max_tasks_per_worker,
            ),
        )
        self._process_manager.start()

    def map(self, func: Callable, args: Iterable) -> List:
        number_of_tasks = 0
        for arg in args:
            self._tasks.put((func, arg))
            number_of_tasks += 1

        # TODO: Return results in sorted order?
        return [self._results.get() for _ in range(number_of_tasks)]

    def close(self):
        self._exit_flag.value = True
        self._process_manager.join()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


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
        return _Task(f"Task {self._id_count}", callable_)

    def add_task(self, callable_: Callable):
        """ Adds the given task to the end of this task manager's queue. """

        if not callable(callable_):
            raise TypeError(
                f"'callable' must of type 'Callable' but was '{type(callable_)}'"
            )

        task = self._create_task(callable_)
        self._tasks.append(task)

    def add_tasks(self, callables: Iterable[Callable]):
        """ Adds the given tasks to the end of this task manager's queue. """
        for callable_ in callables:
            self.add_task(callable_)

    def run(self):
        """ Runs this task manager's tasks and returns the results. """
        with _Pool(
            workers=self._workers, max_tasks_per_worker=self._max_tasks_per_worker
        ) as pool:
            results = pool.map(_task_runner, self._tasks)
        self._tasks.clear()
        return results
