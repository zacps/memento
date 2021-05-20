from sqlite3 import Connection
from unittest.mock import Mock
import pytest
from memento.task_interface import Context, FileSystemCheckpointing
import os
import tempfile
import cloudpickle


def constant_key_provider(
    *args, **kwargs
):  # Necessary to ensure that mocks are not pickled
    return "key"


def arbitrary_expensive_thing(x):
    return x


def arbitrary_expensive_thing2(x):
    return x + 1


class TestContext:
    class TestCheckpoint:
        def setup_method(self, method):
            file = tempfile.NamedTemporaryFile(
                suffix="_memento.checkpoint", delete=False
            )
            self._filepath = os.path.abspath(file.name)
            file.close()

        def teardown_method(self, method):
            os.unlink(self._filepath)

        def test_file_system_checkpoint_provider_checkpoint_works(self):
            checkpoint_provider = FileSystemCheckpointing()
            intermediate = arbitrary_expensive_thing(1)
            context = Context("key", checkpoint_provider)

            context.checkpoint(intermediate)

            assert checkpoint_provider.contains("key")

        def test_file_system_checkpoint_provider_restore_works(self):
            checkpoint_provider = FileSystemCheckpointing()
            intermediate = arbitrary_expensive_thing(1)
            context = Context("key", checkpoint_provider)

            context.checkpoint(intermediate)
            value = context.restore()

            assert value == 1

        def test_file_system_checkpoint_provider_checkpoint_removed(self):
            checkpoint_provider = FileSystemCheckpointing()
            intermediate = arbitrary_expensive_thing(1)
            context = Context("key", checkpoint_provider)

            context.checkpoint(intermediate)
            context.remove_checkpoints("key")

            assert checkpoint_provider.contains("key") is False

        def test_file_system_checkpoint_provider_creates_correct_keys(self):
            def function(*args):
                return args

            context_key = "key"
            arguments = ("test1", "test2", 123, True)
            keyword_arguments = {
                "key1": "value1",
                "key2": "value2",
                "key3": 321,
                "key4": False,
            }
            expected = cloudpickle.dumps(
                {
                    "function": function,
                    "context_key": context_key,
                    "args": arguments,
                    "kwargs": keyword_arguments,
                }
            )

            connection = Mock(spec_set=Connection)
            checkpoint_provider = FileSystemCheckpointing(connection=connection)
            actual = checkpoint_provider.make_key(
                function, context_key, *arguments, **keyword_arguments
            )

            assert expected == actual

        def test_file_system_checkpoint_provider_get_raises_key_error_when_key_not_in_database(
            self,
        ):
            connection = Mock(spec_set=Connection)
            connection.execute().fetchall.return_value = None
            checkpoint_provider = FileSystemCheckpointing(connection=connection)

            with pytest.raises(KeyError) as error_info:
                checkpoint_provider.get("not_in_checkpoint")
