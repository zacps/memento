from io import StringIO

from memento.notifications import FileSystemNotificationProvider


class TestFileSystemNotificationProvider:
    def setup_method(self):
        self.file = StringIO()
        self.provider = FileSystemNotificationProvider(filepath=self.file)

    def test_writes_to_file_on_job_completion(self):
        self.provider.job_completion()
        assert self.file.getvalue() == "Job completed\n"

    def test_writes_to_file_on_task_completion(self):
        self.provider.task_completion()
        assert self.file.getvalue() == "All jobs completed\n"

    def test_writes_to_file_on_task_failure(self):
        self.provider.task_failure()
        assert self.file.getvalue() == "Job failed\n"
