"""Inicializa a conexão com o Redis usada pela aplicação."""

import os
from redis import Redis


class DummyRedis:
    """Redis stand-in used during tests when no server is available."""

    def ping(self):
        return True

    def setex(self, *args, **kwargs):
        return True

    def get(self, *args, **kwargs):
        return None


def init_redis(app=None):
    """Cria o cliente Redis e o registra opcionalmente no app."""
    url = (
        app.config.get("REDIS_URL")
        if app is not None
        else os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )

    if os.getenv("DISABLE_REDIS") == "1":
        client = DummyRedis()
    else:
        client = Redis.from_url(url)
        client.ping()

    if app is not None:
        app.redis_conn = client
    return client


redis_conn = init_redis()

