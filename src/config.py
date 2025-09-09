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

    # E-mail settings (new names with fallback to legacy MAIL_* variables)
    EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "GMAIL")
    EMAIL_FROM = os.getenv(
        "EMAIL_FROM", os.getenv("MAIL_DEFAULT_SENDER", "")
    )
    EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Conecta SENAI")

    if EMAIL_PROVIDER == "GMAIL":
        SMTP_SERVER = os.getenv(
            "SMTP_SERVER", os.getenv("MAIL_SERVER", "smtp.gmail.com")
        )
        SMTP_PORT = int(
            os.getenv("SMTP_PORT", os.getenv("MAIL_PORT", "587"))
        )
    else:  # OUTLOOK or any other provider defaults to Outlook settings
        SMTP_SERVER = os.getenv(
            "SMTP_SERVER", os.getenv("MAIL_SERVER", "smtp.office365.com")
        )
        SMTP_PORT = int(
            os.getenv("SMTP_PORT", os.getenv("MAIL_PORT", "587"))
        )
    SMTP_USERNAME = os.getenv(
        "SMTP_USERNAME", os.getenv("MAIL_USERNAME", "")
    )
    SMTP_PASSWORD = os.getenv(
        "SMTP_PASSWORD", os.getenv("MAIL_PASSWORD", "")
    )
    SMTP_USE_TLS = env_bool(
        "SMTP_USE_TLS", env_bool("MAIL_USE_TLS", True)
    )
    SMTP_USE_SSL = env_bool(
        "SMTP_USE_SSL", env_bool("MAIL_USE_SSL", False)
    )
    SMTP_TIMEOUT = int(
        os.getenv("SMTP_TIMEOUT", os.getenv("MAIL_TIMEOUT", "15"))
    )
    CLIENT_ID = os.getenv("CLIENT_ID", "")
    TENANT_ID = os.getenv("TENANT_ID", "")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
    EMAIL_SMTP_VALIDATE_ON_STARTUP = env_bool(
        "EMAIL_SMTP_VALIDATE_ON_STARTUP", False
    )

    # Legacy aliases to avoid breaking old code paths
    MAIL_SERVER = SMTP_SERVER
    MAIL_PORT = SMTP_PORT
    MAIL_USE_TLS = SMTP_USE_TLS
    MAIL_USE_SSL = SMTP_USE_SSL
    MAIL_USERNAME = SMTP_USERNAME
    MAIL_PASSWORD = SMTP_PASSWORD
    MAIL_DEFAULT_SENDER = EMAIL_FROM
    MAIL_TIMEOUT = SMTP_TIMEOUT

    SECURITY_PASSWORD_SALT = os.environ.get(
        'SECURITY_PASSWORD_SALT', 'change-me'
    )
    FRONTEND_BASE_URL = os.getenv(
        'FRONTEND_BASE_URL', 'http://localhost:5000'
    )
    APP_BASE_URL = os.getenv(
        'APP_BASE_URL', 'https://conecta-senai.up.railway.app'
    )

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    RATELIMIT_STORAGE_URI = os.getenv(
        "RATELIMIT_STORAGE_URI", f"redis://{REDIS_HOST}:{REDIS_PORT}"
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
