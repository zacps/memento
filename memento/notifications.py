"""
Contains classes for progress reporting.
"""
from abc import ABC, abstractmethod
from typing import Union, TextIO


class NotificationProvider(ABC):
    """
    Abstract base class for implementing a notification provider, allowing notifications to be
    raised to different locations. Generally, you should inherit from
    :class:`DefaultNotificationProvider` to avoid having to implement every method.
    """

    @abstractmethod
    def job_completion(self):
        """
        Executed when a task completes.
        """

    @abstractmethod
    def task_completion(self):
        """
        Executed when all tasks complete.
        """

    @abstractmethod
    def task_failure(self):
        """
        Executed when a task fails to execute.
        """


class DefaultNotificationProvider(NotificationProvider):
    """
    Default :class:`NotificationProvider` implementation that takes no actions when an event
    occurs. This is the class you should extend if you want to create your own custom
    notification provider.
    """

    def job_completion(self):
        pass

    def task_completion(self):
        pass

    def task_failure(self):
        pass


class ConsoleNotificationProvider(DefaultNotificationProvider):
    """
    Writes notification to the console (stdout).
    """

    def job_completion(self):
        print("Job completed")

    def task_completion(self):
        print("All jobs completed")

    def task_failure(self):
        print("Job failed")


class FileSystemNotificationProvider(DefaultNotificationProvider):
    """
    Writes notifications to a file.
    """

    def __init__(self, filepath: Union[TextIO, str] = None):
        """
        Creates a FileSystemNotificationProvider.

        :param filepath: the filepath to write notifications to, opened in append mode,
        or a file-like object. Defaults to 'logs.txt'.
        """
        self._filepath = filepath or "logs.txt"
        self._is_file = not isinstance(filepath, str)

    def _write(self, message: str):
        s = f"{message}\n"
        if self._is_file:
            self._filepath.write(s)
        else:
            with open(self._filepath, "a") as file:
                file.write(s)

    def job_completion(self):
        self._write("Job completed")

    def task_completion(self):
        self._write("All jobs completed")

    def task_failure(self):
        self._write("Job failed")
