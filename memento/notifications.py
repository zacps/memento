"""

"""
from abc import ABC, abstractmethod


class NotificationProvider(ABC):
    """

    """

    @abstractmethod
    def job_completion(self):
        """

        """

    @abstractmethod
    def task_completion(self):
        """

        """

    @abstractmethod
    def task_failure(self):
        """

        """


class ConsoleNotificationProvider(NotificationProvider):
    def job_completion(self):
        print("Job completed")

    def task_completion(self):
        print("All jobs completed")

    def task_failure(self):
        print("Job failed")
