"""

"""
from abc import ABC, abstractmethod


class NotificationProvider(ABC):
    """
    Abstract base class for implementing a notification provider, allowing different
    forms of notifications to be raised.

    Provides the interface that all cache providers must adhere to.

    Must be used as the parent class of a cache provider class.

    ..
        class CustomCacheProvider(CacheProvider):
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
    def job_completion(self):
        pass

    def task_completion(self):
        pass

    def task_failure(self):
        pass


class ConsoleNotificationProvider(DefaultNotificationProvider):
    def job_completion(self):
        print("Job completed")

    def task_completion(self):
        print("All jobs completed")

    def task_failure(self):
        print("Job failed")


class FileSystemNotificationProvider(DefaultNotificationProvider):
    def __init__(self, filename: str = None):
        self._filename = filename or "logs.txt"

    def _write(self, message: str):
        with open(self._filename, 'a') as f:
            f.write(f'{message}\n')

    def job_completion(self):
        self._write("Job completed")

    def task_completion(self):
        self._write("All jobs completed")

    def task_failure(self):
        self._write("Job failed")
