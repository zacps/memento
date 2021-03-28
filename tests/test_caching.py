from unittest.mock import Mock
import pytest
import cloudpickle
from memento.caching import Cache, MemoryCacheProvider, CacheProvider


class TestCache:
    def test_cache_calls_underlying_function_when_not_in_cache(self):
        underlying_func = Mock()
        cache_provider = Mock(spec_set=CacheProvider)
        cache_provider.get.side_effect = KeyError()

        cached = Cache(underlying_func, cache_provider)
        cached({"key1": "value1"})
        underlying_func.assert_called_with({"key1": "value1"})

    def test_cache_does_not_execute_already_cached_function(self):
        underlying_func = Mock()
        cache_provider = Mock(spec_set=CacheProvider)
        cache_provider.contains.return_value = True
        cached_function = Cache(underlying_func, cache_provider=cache_provider)

        cached_function()

        underlying_func.assert_not_called()

    def test_cache_saves_function_result_if_not_in_cache(self):
        result = "result"
        cache_key = "not_in_cache"
        underlying_func = Mock(return_value=result)
        cache_provider = Mock(spec_set=CacheProvider)
        cache_provider.make_key.return_value = cache_key
        cache_provider.get.side_effect = KeyError()

        cached_function = Cache(underlying_func, cache_provider=cache_provider)

        cached_function()

        cache_provider.set.assert_called_once_with(cache_key, result)

    def test_cache_creates_memory_cache_provider_by_default(self):
        cache = Cache(lambda x: x + 1)
        assert isinstance(cache._cache_provider, MemoryCacheProvider)


class TestMemoryCacheProvider:
    def test_memory_cache_provider_get_works_when_data_in_cache(self):
        provider = MemoryCacheProvider({"key": "value"})
        value = provider.get("key")
        assert value == "value"

    def test_memory_cache_provider_set_works(self):
        provider = MemoryCacheProvider()
        provider.set("key", "value")
        assert provider._cache.get("key") == "value"

    def test_memory_cache_provider_contains_works(self):
        provider = MemoryCacheProvider({"key": "value"})
        assert provider.contains("key") is True
        assert provider.contains("not_in_cache") is False

    def test_memory_cache_provider_creates_initial_empty_cache(self):
        provider = MemoryCacheProvider()
        assert provider._cache == {}

    def test_memory_cache_provider_creates_initial_cache_when_provided(self):
        initial_cache = {"key1": "value1", "key2": 123}
        provider = MemoryCacheProvider(initial_cache)
        assert provider._cache == initial_cache

    def test_memory_cache_provider_creates_correct_keys(self):
        def function(*args):
            return args

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
                "args": arguments,
                "kwargs": keyword_arguments,
            }
        )

        provider = MemoryCacheProvider()
        actual = provider.make_key(function, *arguments, **keyword_arguments)

        assert expected == actual

    def test_memory_cache_provider_raises_keyError_when_key_not_in_cache(self):
        provider = MemoryCacheProvider()
        with pytest.raises(KeyError) as error_info:
            provider.get("not_in_cache")
