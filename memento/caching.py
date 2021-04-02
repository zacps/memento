"""
Contains classes for implementing caching of functions.
"""
import os
import sqlite3
import tempfile
from abc import ABC, abstractmethod
from typing import Callable
import cloudpickle


class CacheProvider(ABC):
    """
    Abstract base class for implementing a cache provider, allowing different forms of caching.

    Provides the interface that all cache providers must adhere to.

    Must be used as the parent class of a cache provider class.

    ..
        class CustomCacheProvider(CacheProvider):
    """

    def __getitem__(self, key: str):
        return self.get(key)

    def __setitem__(self, key: str, item):
        return self.set(key, item)

    def __contains__(self, key: str):
        return self.contains(key)

    @abstractmethod
    def __str__(self) -> str:
        """
        Creates a human-readable string of the cache.

        :return: A string representing the cache.
        """

    @abstractmethod
    def get(self, key: str):
        """
        Gets the item in the cache specified by the key.

        :param key: Used to get the item from the cache.
        :returns: The item in the cache, if it exists.
        :raise KeyError: When the key is not in the cache.
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
        self._cache = initial_cache or {}

    def __str__(self):
        return str(self._cache)

    def get(self, key: str):
        return self._cache[key]

    def set(self, key: str, item) -> None:
        self._cache[key] = item

    def contains(self, key: str) -> bool:
        return self._cache.get(key, False) is not False

    def make_key(self, func: Callable, *args, **kwargs) -> str:
        return cloudpickle.dumps({"function": func, "args": args, "kwargs": kwargs})


class FileSystemCacheProvider(CacheProvider):
    def __init__(self, connection: sqlite3.Connection = None, filepath: str = None):
        self._connection = connection
        self._filepath = filepath or tempfile.TemporaryFile().name  # create temporary file

        self.SQLITE_TIMESTAMP = "(julianday('now') - 2440587.5)*86400.0"
        self.sql_select = f"SELECT value FROM cache WHERE key = ?"
        self.sql_insert = "INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)"

        self._create_db()

    def _create_db(self) -> None:
        with self as db:
            db.execute(f"""
                CREATE TABLE IF NOT EXISTS cache (
                    key BINARY PRIMARY KEY,
                    ts REAL NOT NULL DEFAULT ({self.SQLITE_TIMESTAMP}),
                    value BLOB NOT NULL
                ) WITHOUT ROWID
            """)

    def __enter__(self) -> sqlite3.Connection:
        return self._connection or sqlite3.connect(self._filepath)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._connection is not None:
            self._connection.close()

    def __del__(self):
        if self._connection is not None:
            self._connection.close()
        os.remove(self._filepath)  # remove the temp file

    def __str__(self) -> str:
        raise NotImplementedError()


    def get(self, key: str):
        with self as db:
            rows = db.execute(self.sql_select, (key,), ).fetchall()
            if rows:
                return rows[0][0]
            else:
                raise KeyError()

    def set(self, key: str, item) -> None:
        with self as db:
            db.execute(self.sql_insert, (key, item))

    def contains(self, key: str) -> bool:
        try:
            self.get(key)
            return True
        except KeyError:
            return False

    def make_key(self, func: Callable, *args, **kwargs) -> str:
        return cloudpickle.dumps({"function": func, "args": args, "kwargs": kwargs})


class Cache:
    """
    A higher order function that caches another, underlying function.
    """

    def __init__(self, func: Callable, cache_provider: CacheProvider = None):
        """
        Create the Cache object.

        Usage can be one of the following:

        ..
            @Cache
            def underlying_function():
                pass

            cached_function = Cache(underlying_function)

        :param func: The function to be cached.
        :param cache_provider: The cache provider, defaults to FileSystemCacheProvider
        """
        self._func = func
        if cache_provider is None:
            cache_provider = FileSystemCacheProvider()
        self._cache_provider = cache_provider

    def __call__(self, *args, **kwargs):
        """
        Method called when the cached function is called.

        ..
            @Cache
            def underlying_func():
                pass
            cached_func = Cache(underlying_func)

            underlying_func()
            cached_func()

        :param args: Arguments to the underlying function.
        :param kwargs: Keyword arguments to the underlying function.
        :return: The (cached) result of the underlying function.
        """
        key = self._cache_provider.make_key(self, self._func, *args, **kwargs)

        try:
            return self._cache_provider.get(key)
        except KeyError:
            value = self._func(*args, **kwargs)  # execute the function, with arguments
            self._cache_provider.set(key, value)
            return value

    def __str__(self):
        """
        Creates a human-readable string of the cache and cached function.

        :return: A string representing the cached function.
        """
        return f"Cached function object: func: {self._func}, cache: {str(self._cache_provider)}"
