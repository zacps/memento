import dill
from typing import Callable
from abc import ABC, abstractmethod


class CacheProvider(ABC):
    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, item):
        return self.set(key, item)

    def __contains__(self, key):
        return self.contains(key)

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def set(self, key, item) -> None:
        pass

    @abstractmethod
    def contains(self, key) -> bool:
        pass

    @abstractmethod
    def make_key(self, func: Callable, *args, **kwargs) -> str:
        pass


class MemoryCacheProvider(CacheProvider):
    def __init__(self, initial_cache: dict = None):
        if initial_cache is None:
            initial_cache = (
                {}
            )  # Explicitly create dictionary here, as otherwise would be externally mutable
        self.cache = initial_cache

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, item) -> None:
        self.cache[key] = item

    def contains(self, key) -> bool:
        return self.cache.get(key, False) is not False

    def make_key(self, func: Callable, *args, **kwargs) -> str:
        return dill.dumps({"function": func, "args": args, "kwargs": kwargs})


class Cache:
    def __init__(self, func: Callable, cache_provider: CacheProvider = None):
        self.func = func
        if cache_provider is None:
            cache_provider = MemoryCacheProvider()
        self.cache_provider = cache_provider

    def __call__(self, *args, **kwargs):
        key = self.cache_provider.make_key(self, self.func, *args, **kwargs)

        if self.cache_provider.contains(key):
            return self.cache_provider.get(key)
        else:
            value = self.func(*args, **kwargs)  # execute the function, with arguments
            self.cache_provider.set(key, value)
            return value
