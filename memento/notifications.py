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


class DefaultNotificationProvider(NotificationProvider):
    def job_completion(self):
        pass

    def task_completion(self):
        pass

    def task_failure(self):
        pass
