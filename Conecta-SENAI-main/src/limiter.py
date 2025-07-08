"""
Inicializa o objeto de limitacao de requisicoes.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

limiter = Limiter(
    get_remote_address,
    storage_uri=os.environ.get("REDIS_URL", "memory://"),
    storage_options={"socket_connect_timeout": 30},
    strategy="fixed-window",
)
