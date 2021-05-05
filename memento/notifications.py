"""
Contains classes for progress reporting.
"""
import email
from email.utils import formataddr
import smtplib
from abc import ABC, abstractmethod
from typing import Union, TextIO, Iterable, NamedTuple


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
        str_ = f"{message}\n"
        if self._is_file:
            self._filepath.write(str_)
        else:
            with open(self._filepath, "a") as file:
                file.write(str_)

    def job_completion(self):
        self._write("Job completed")

    def task_completion(self):
        self._write("All jobs completed")

    def task_failure(self):
        self._write("Job failed")


class SmtpConfiguration(NamedTuple):
    """ SMTP server configuration options used by :class:`EmailNotificationProvider`. """

    host: str
    """ SMTP server host. """

    port: int
    """ SMTP server port. """

    username: str = None
    """ Username to authenticate with. """

    password: str = None
    """ Password to authenticate with. """

    require_tls: bool = True
    """ Whether to require a TLS connection. Defaults to True. """


class EmailNotificationProvider(DefaultNotificationProvider):
    """
    Sends notifications via email. Requires an SMTP server to connect to.

    For example, to send notifications using a Gmail account::

        smtp_config = SmtpConfiguration(
            'smtp.gmail.com',
            587,
            username='sender@gmail.com',
            password='password'
        )

        self.provider = EmailNotificationProvider(
            smtp_config,
            "sender@gmail.com",
            ["recipient@gmail.com"]
        )
    """

    def __init__(
        self,
        smtp: Union[SmtpConfiguration, smtplib.SMTP],
        from_addr: str,
        to_addrs: Iterable[str],
    ):
        """
        Creates an EmailNotificationProvider.

        :param smtp: SMTP configuration or a smtplib.SMTP object
        :param from_addr: email address emails will be sent from
        :param to_addrs: email addresses emails will be sent to
        """
        self._smpt_config = smtp
        self._client = smtp if isinstance(smtp, smtplib.SMTP) else None
        self._from_addr = from_addr
        self._to_addrs = to_addrs

    @property
    def smpt(self):
        """ This provider's SmtpConfiguration. """
        return self._smpt_config

    @property
    def from_addr(self):
        """ Email address emails will be sent from. """
        return self._from_addr

    @property
    def to_addrs(self):
        """ Email addresses emails will be sent to. """
        return self._to_addrs

    def _send_email(self, message: email.message.Message):
        if self._client:
            self._client.send_message(message)
        else:
            with smtplib.SMTP(self._smpt_config.host, self._smpt_config.port) as smtp:
                try:
                    smtp.starttls()
                except smtplib.SMTPNotSupportedError as error:
                    if self._smpt_config.require_tls:
                        raise error

                if self._smpt_config.username:
                    smtp.login(self._smpt_config.username, self._smpt_config.password)
                smtp.send_message(message)

    def create_message(self, subject: str, content: str) -> email.message.Message:
        """ Creates an :class:`email.message.Message` with the given subject and content. """
        message = email.message.EmailMessage()
        message["From"] = formataddr(("Memento", self._from_addr))
        message["To"] = ",".join(self._to_addrs)
        message["Subject"] = subject
        message.set_content(
            content
        )  # TODO: Maybe support HTML messages with a plain text fallback
        return message

    def job_completion(self):
        message = self.create_message("[Memento] Job completed", "Job completed")
        self._send_email(message)

    def task_completion(self):
        message = self.create_message(
            "[Memento] All jobs completed", "All jobs completed"
        )
        self._send_email(message)

    def task_failure(self):
        message = self.create_message("[Memento] Job failed", "Job failed")
        self._send_email(message)
