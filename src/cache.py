from flask_caching import Cache
from src.redis_client import redis_conn, DummyRedis

cache = Cache()

def init_cache(app):
    """Initialize cache using Redis when available."""
    if isinstance(redis_conn, DummyRedis):
        config = {"CACHE_TYPE": "SimpleCache"}
    else:
        config = {
            "CACHE_TYPE": "RedisCache",
            "CACHE_REDIS_URL": app.config.get("REDIS_URL"),
        }
    cache.init_app(app, config=config)
    return cache
