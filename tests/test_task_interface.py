from unittest.mock import Mock, MagicMock

import cloudpickle as cloudpickle

from memento.caching import CacheProvider, FileSystemCacheProvider
from memento.task_interface import Context


class TestContext:
    class TestCheckpoint:
        def test_checkpoint_doesnt_call_function_if_in_cache(self):
            def no_pickle_key(x, *y, **z):
                return "key"

            expensive_thing = MagicMock()

            cache_provider = Mock(spec_set=CacheProvider)
            cache_provider.make_key = no_pickle_key
            cache_provider.get.return_value = expensive_thing

            context = Context("key", cache_provider)

            def experiment():
                return context.checkpoint(expensive_thing)()

            experiment()

            expensive_thing.assert_not_called()

        def test_checkpoint_calls_underlying_function_once(self):
            total_calls = []

            def expensive_thing(calls: list[int]):
                calls.append(1)

            def constant_key(*args, **kwargs):
                return "key"

            cache_provider = FileSystemCacheProvider(key=constant_key, table_name="checkpoint")
            context = Context("key", cache_provider)

            def experiment():
                return context.checkpoint(expensive_thing)(total_calls)

            experiment()
            experiment()

            assert len(total_calls) == 1
