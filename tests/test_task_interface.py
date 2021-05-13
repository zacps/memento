import sqlite3
from unittest.mock import Mock, MagicMock
import pytest
from memento.caching import CacheProvider, FileSystemCacheProvider, default_key_provider
from memento.memento import remove_checkpoints
from memento.task_interface import Context


def constant_key_provider(
    *args, **kwargs
):  # Necessary to ensure that mocks are not pickled
    return "key"


def arbitrary_expensive_thing(x):
    return x


class TestContext:
    class TestCheckpoint:
        def test_checkpoint_doesnt_call_function_if_in_cache(self):
            expensive_thing = MagicMock()

            cache_provider = Mock(spec_set=CacheProvider)
            cache_provider.make_key = constant_key_provider
            cache_provider.get.return_value = expensive_thing

            context = Context("key", cache_provider)

            def experiment():
                return context.checkpoint(expensive_thing)()

            experiment()

            expensive_thing.assert_not_called()

        def test_checkpoint_calls_underlying_function_once(self):
            total_calls = []

            # Need to pass an object by reference to track the number of calls
            # This is a workaround as Mocks cannot be pickled/unpickled
            def expensive_thing(calls: list[int]):
                calls.append(1)

            cache_provider = FileSystemCacheProvider(
                key_provider=constant_key_provider, table_name="checkpoint"
            )
            context = Context("key", cache_provider)

            def experiment():
                context.checkpoint(expensive_thing)(total_calls)

            experiment()
            experiment()

            assert len(total_calls) == 1

        def test_checkpoint_saves_multiple_checkpoints(self):

            cache_provider = FileSystemCacheProvider(table_name="checkpoint")
            context = Context("key", cache_provider)

            def experiment():
                context.checkpoint(arbitrary_expensive_thing)(1)
                context.checkpoint(arbitrary_expensive_thing)(2)

            experiment()

            assert cache_provider.contains(
                default_key_provider(arbitrary_expensive_thing, 1)
            )
            assert cache_provider.contains(
                default_key_provider(arbitrary_expensive_thing, 2)
            )

        def test_checkpoint_cleans_up(self):
            cache_provider = FileSystemCacheProvider(table_name="key_checkpoint")
            context = Context("key", cache_provider)

            def experiment():
                context.checkpoint(arbitrary_expensive_thing)(1)
                context.checkpoint(arbitrary_expensive_thing)(2)

            experiment()
            remove_checkpoints(cache_provider, "key")

            with pytest.raises(sqlite3.OperationalError) as error:
                context.checkpoint(arbitrary_expensive_thing)(1)
                assert str(error.info) == "no such table: key_checkpoint"

        def test_multiple_checkpoint_deletion(self):
            cache_provider = FileSystemCacheProvider(table_name="key_checkpoint")
            context = Context("key", cache_provider)
            cache_provider_2 = FileSystemCacheProvider(table_name="key2_checkpoint")
            context_2 = Context("key2", cache_provider_2)

            def experiment():
                context.checkpoint(arbitrary_expensive_thing)(1)
                context_2.checkpoint(arbitrary_expensive_thing)(1)

            experiment()
            remove_checkpoints(cache_provider, "key")
            remove_checkpoints(cache_provider_2, "key2")

            with pytest.raises(sqlite3.OperationalError) as error:
                context.checkpoint(arbitrary_expensive_thing)(1)
                context_2.checkpoint(arbitrary_expensive_thing)(1)
                assert str(error.info) == "no such table: key_checkpoint"
