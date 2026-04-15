from functools import wraps
from typing import Callable, Any
import time
import hashlib
import json

class Cache:
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def _key(self, *args, **kwargs) -> str:
        key = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str) -> Any:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        if len(self.cache) >= self.max_size:
            oldest = min(self.cache.items(), key=lambda x: x[1][1])
            del self.cache[oldest[0]]
        self.cache[key] = (value, time.time())
    
    def memoize(self, fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = self._key(*args, **kwargs)
            result = self.get(key)
            if result is None:
                result = fn(*args, **kwargs)
                self.set(key, result)
            return result
        return wrapper

cache = Cache()

# Usage: @cache.memoize
def expensive_function(x):
    time.sleep(1)  # simulate work
    return x * 2