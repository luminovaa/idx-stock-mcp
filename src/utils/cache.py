"""Simple caching utility using cachetools."""

from cachetools import TTLCache

# Cache configurations (maxsize, ttl in seconds)
price_cache = TTLCache(maxsize=500, ttl=300)  # 5 minutes
technical_cache = TTLCache(maxsize=500, ttl=14400)  # 4 hours
fundamental_cache = TTLCache(maxsize=500, ttl=86400)  # 24 hours
money_flow_cache = TTLCache(maxsize=500, ttl=14400)  # 4 hours
news_cache = TTLCache(maxsize=200, ttl=1800)  # 30 minutes
macro_cache = TTLCache(maxsize=50, ttl=3600)  # 1 hour


def get_cache_key(*args) -> str:
    """Generate a cache key from arguments."""
    return ":".join(str(a) for a in args)
