"""
Contains classes for implementing caching of functions.
"""
from abc import ABC, abstractmethod
from typing import Callable
import dill


class CacheProvider(ABC):
    """
    Abstract base class for implementing a cache provider, allowing different forms of caching.

    Provides the interface that all cache providers must adhere to.

    Must be used as the parent class of a cache provider class.

    ``
    class CustomCacheProvider(CacheProvider):
    ``
    """

    def __getitem__(self, key: str):
        return self.get(key)

    def __setitem__(self, key: str, item):
        return self.set(key, item)

    def __contains__(self, key: str):
        return self.contains(key)

    @abstractmethod
    def get(self, key: str):
        """
        Gets the item in the cache specified by the key.

        :param key: Used to get the item from the cache.
        :returns: The item in the cache, if it exists.
        """

    @abstractmethod
    def set(self, key: str, item) -> None:
        """
        Puts the item in the cache, at the specified key.

        :param key: The location for the item in the cache.
        :param item: The item to be cached.
        :returns: Nothing.
        """

    @abstractmethod
    def contains(self, key: str) -> bool:
        """
        Checks whether a key is already in the cache.

        :param key: The key to check.
        :returns: True if it exists, False otherwise.
        """

    @abstractmethod
    def make_key(self, func: Callable, *args, **kwargs) -> str:
        """
        Generates a key to be used in caching.

        :param func: The function to be cached.
        :param args: Arguments to the function to be cached.
        :param kwargs: Keyword arguments to the function to be cached.
        :returns: True if it exists, False otherwise.
        """


class MemoryCacheProvider(CacheProvider):
    """
    An in-memory cache provider. Uses a dictionary for underlying storage.
    """

    def __init__(self, initial_cache: dict = None):
        """
        Creates a cache provider that uses memory for caching.

        :param initial_cache: Optional initial cache, defaults to an empty dictionary.
        """
        if initial_cache is None:
            # Explicitly create dictionary here, as otherwise would be externally mutable
            initial_cache = {}
        self.cache = initial_cache

    def get(self, key: str):
        return self.cache.get(key)

    def set(self, key: str, item) -> None:
        self.cache[key] = item

    def contains(self, key: str) -> bool:
        return self.cache.get(key, False) is not False

    def make_key(self, func: Callable, *args, **kwargs) -> str:
        return dill.dumps({"function": func, "args": args, "kwargs": kwargs})


class Cache:
    """
    A higher order function that caches another, underlying function.
    """

    def __init__(self, func: Callable, cache_provider: CacheProvider = None):
        """
        Create the Cache object.

        Usage can be one of the following:
        ``
        @Cache
        def underlying_function():
            pass
        ``

        ``
        cached_function = Cache(underlying_function)
        ``

        :param func: The function to be cached.
        :param cache_provider: The cache provider, defaults to MemoryCacheProvider
        """
        self.func = func
        if cache_provider is None:
            cache_provider = MemoryCacheProvider()
        self.cache_provider = cache_provider

    def __call__(self, *args, **kwargs):
        """
        Method called when the cached function is called.

        ``
        @Cache
        def underlying_func:
            pass
        cached_func = Cache(underlying_func)

        underlying_func()
        cached_func
        ``

        :param args: Arguments to the underlying function.
        :param kwargs: Keyword arguments to the underlying function.
        :return: The (cached) result of the underlying function.
        """
        key = self.cache_provider.make_key(self, self.func, *args, **kwargs)

        if self.cache_provider.contains(key):
            return self.cache_provider.get(key)

        value = self.func(*args, **kwargs)  # execute the function, with arguments
        self.cache_provider.set(key, value)
        return value

    def __str__(self):
        """
        Creates a human-readable string of the cache and cached function.

        :return: A string representing the cached function.
        """
        return f"Cached function object: func: {self.func}, cache: {str(self.cache_provider.cache)}"
