import logging
import os


def strtobool(val: str) -> int:
    """Convert a string representation of truth to ``1`` or ``0``.

    This mirrors :func:`distutils.util.strtobool`, which was removed in
    Python 3.12.  Recognised values are::

        "y", "yes", "t", "true", "on", "1"  ->  ``1``
        "n", "no", "f", "false", "off", "0" ->  ``0``

    Any other value results in a :class:`ValueError`.
    """

    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return 1
    if val in ("n", "no", "f", "false", "off", "0"):
        return 0
    raise ValueError(f"invalid truth value {val}")


def env_bool(name: str, default: bool = False) -> bool:
    """Read an environment variable as boolean.

    Accepts many common string representations ("true", "0", "yes", ...).
    Falls back to ``default`` if parsing fails.
    """
    v = os.getenv(name, str(default))
    try:
        return bool(strtobool(str(v)))
    except Exception:
        return bool(default)


class BaseConfig:
    """Base configuration with default settings."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = logging.INFO

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = env_bool("MAIL_USE_TLS", True)
    MAIL_USE_SSL = env_bool("MAIL_USE_SSL", False)
    MAIL_SUPPRESS_SEND = env_bool("MAIL_SUPPRESS_SEND", False)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER", "no-reply@conecta-senai"
    )
    MAIL_TIMEOUT = int(os.getenv("MAIL_TIMEOUT", "12"))
    SECURITY_PASSWORD_SALT = os.environ.get(
        'SECURITY_PASSWORD_SALT', 'change-me'
    )
    FRONTEND_BASE_URL = os.getenv(
        'FRONTEND_BASE_URL', 'http://localhost:5000'
    )
    APP_BASE_URL = os.getenv(
        'APP_BASE_URL', 'https://conecta-senai.up.railway.app'
    )


class DevConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = logging.DEBUG


class ProdConfig(BaseConfig):
    """Production configuration."""
    LOG_LEVEL = logging.INFO


class TestConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    LOG_LEVEL = logging.WARNING
