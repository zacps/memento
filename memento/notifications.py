"""
Contains classes for progress reporting.
"""
from abc import ABC, abstractmethod


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

    def __init__(self, filename: str = None):
        """
        Creates a FileSystemNotificationProvider.

        :param filename: the file to write notifications to, opened in append mode.
        """
        self._filename = filename or "logs.txt"

    def _write(self, message: str):
        with open(self._filename, "a") as file:
            file.write(f"{message}\n")

    def job_completion(self):
        self._write("Job completed")

    def task_completion(self):
        self._write("All jobs completed")

    def task_failure(self):
        self._write("Job failed")
