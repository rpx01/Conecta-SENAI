"""
Fornece conexao com Redis, usando DummyRedis quando o servidor nao esta disponivel.
"""
import os
import time

try:
    from redis import Redis
except ImportError:  # pragma: no cover - pacote redis ausente
    Redis = None

class DummyRedis:
    """Implementacao em memoria usada quando o servidor Redis nao esta disponivel."""

    def __init__(self):
        self.store = {}

    def setex(self, name, time_delta, value):
        seconds = int(time_delta.total_seconds()) if hasattr(time_delta, "total_seconds") else int(time_delta)
        expire_at = int(time.time()) + seconds
        self.store[name] = (value, expire_at)

    def get(self, name):
        item = self.store.get(name)
        if not item:
            return None
        value, exp = item
        if exp < time.time():
            self.store.pop(name, None)
            return None
        return value


def _create_client():
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    if Redis is not None:
        try:
            client = Redis.from_url(url)
            client.ping()
            return client
        except Exception:
            pass
    return DummyRedis()


redis_conn = _create_client()
