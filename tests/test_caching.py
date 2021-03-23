from typing import Callable
from unittest import mock

import dill

from memento.caching import Cache, MemoryCacheProvider, CacheProvider


class MockCacheProvider(CacheProvider):
    def get(self, key):
        pass

    def set(self, key, item):
        pass

    def contains(self, key):
        pass

    def make_key(self, func: Callable, *args, **kwargs) -> str:
        pass


class TestCache:
    def test_cache_calls_underlying_function_when_not_in_cache(self):
        underlying_func = mock.MagicMock()
        provider = MockCacheProvider()
        provider.make_key = mock.MagicMock(
            return_value="not-in-cache"
        )  # can't pickle a MagicMock
        provider.contains = mock.MagicMock(return_value=False)

        cached = Cache(underlying_func, provider)
        cached({"key1": "value1"})
        underlying_func.assert_called_with({"key1": "value1"})

    def test_cache_does_not_execute_already_cached_function(self):
        underlying_func = mock.MagicMock()
        cache_key = "cache-key"
        cached_result = "result"
        provider = MockCacheProvider()

        provider.make_key = mock.MagicMock(
            return_value=cache_key
        )  # can't pickle a MagicMock
        provider.contains = mock.MagicMock(return_value=True)
        provider.get = mock.MagicMock(return_value=cached_result)
        cached_function = Cache(underlying_func, cache_provider=provider)

        resp = cached_function("test")

        provider.contains.assert_called_with(cache_key)
        provider.get.assert_called_with(cache_key)
        underlying_func.assert_not_called()
        assert resp == cached_result

    def test_cache_saves_function_result_if_not_in_cache(self):
        result = "result"
        underlying_func = mock.MagicMock(return_value=result)
        provider = MockCacheProvider()
        cache_key = "not_in_cache"

        provider.make_key = mock.MagicMock(
            return_value=cache_key
        )  # can't pickle a MagicMock
        provider.set = mock.MagicMock()
        cached_function = Cache(underlying_func, cache_provider=provider)

        cached_function()

        provider.set.assert_called_once_with(cache_key, result)

    def test_cache_creates_memory_cache_provider_by_default(self):
        cache = Cache(lambda x: x + 1)
        assert isinstance(cache.cache_provider, MemoryCacheProvider)


class TestMemoryCacheProvider:
    def test_memory_cache_provider_get_works_when_data_in_cache(self):
        provider = MemoryCacheProvider({"key": "value"})
        value = provider.get("key")
        assert value == "value"

    def test_memory_cache_provider_set_works(self):
        provider = MemoryCacheProvider()
        provider.set("key", "value")
        assert provider.cache.get("key") == "value"

    def test_memory_cache_provider_contains_works(self):
        provider = MemoryCacheProvider({"key": "value"})
        assert provider.contains("key") is True
        assert provider.contains("not_in_cache") is False

    def test_memory_cache_provider_creates_initial_empty_cache(self):
        provider = MemoryCacheProvider()
        assert provider.cache == {}

    def test_memory_cache_provider_creates_initial_cache_when_provided(self):
        initial_cache = {"key1": "value1", "key2": 123}
        provider = MemoryCacheProvider(initial_cache)
        assert provider.cache == initial_cache

    def test_memory_cache_provider_creates_correct_keys(self):
        def function(x):
            return x

        args = ("test1", "test2", 123, True)
        kwargs = {"key1": "value1", "key2": "value2", "key3": 321, "key4": False}
        expected = dill.dumps(
            {
                "function": function,
                "args": args,
                "kwargs": kwargs,
            }
        )

        provider = MemoryCacheProvider()
        actual = provider.make_key(function, *args, **kwargs)

        assert expected == actual
