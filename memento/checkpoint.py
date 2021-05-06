"""
Contains class to enable checkpointing features in case of failed tests
"""
import os
import tempfile
import cloudpickle


class Checkpoint:
    """
    Save the current state of the task
    """
    def __init__(self, data, key):
        """
        For each checkpoint, it is saved in a new file
        """
        self.data = data
        self.key = key

    def save(self, path=None):
        """Save data to a pickle located at `path`"""
        if path is None:

            path = os.path.abspath(
                path or tempfile.NamedTemporaryFile(suffix="_memento.checkpoint").name
            )
        with open(path, "wb") as save_file:
            cloudpickle.dump((self.data, self.key), save_file)

    def load(self, path=None):
        """Load data back from 'path'"""
