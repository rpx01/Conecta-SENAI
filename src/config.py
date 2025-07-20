"""Application configuration classes."""

from __future__ import annotations

import os


def _database_uri() -> str:
    """Return the SQLAlchemy database URI from environment.

    Replaces the deprecated ``postgres://`` prefix with ``postgresql://`` and
    falls back to a local SQLite file when ``DATABASE_URL`` is not provided.
    """
    url = os.getenv("DATABASE_URL", "")
    if not url:
        return "sqlite:///agenda_laboratorio.db"
    return url.replace("postgres://", "postgresql://")


class BaseConfig:
    """Base configuration shared across environments."""

    SECRET_KEY = (
        os.getenv("SECRET_KEY")
        or os.getenv("FLASK_SECRET_KEY", "changeme")
    )
    FLASK_SECRET_KEY = SECRET_KEY

    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    RECAPTCHA_SITE_KEY = (
        os.getenv("RECAPTCHA_SITE_KEY")
        or os.getenv("SITE_KEY", "")
    )
    RECAPTCHA_SECRET_KEY = (
        os.getenv("RECAPTCHA_SECRET_KEY")
        or os.getenv("CAPTCHA_SECRET_KEY")
        or SECRET_KEY
    )
    RECAPTCHA_THRESHOLD = float(os.getenv("RECAPTCHA_THRESHOLD", "0.5"))


class DevelopmentConfig(BaseConfig):
    """Configuration used during local development."""

    DEBUG = True


class TestingConfig(BaseConfig):
    """Configuration for running the test suite."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    """Configuration for production deployment."""

    DEBUG = False


__all__ = [
    "BaseConfig",
    "DevelopmentConfig",
    "TestingConfig",
    "ProductionConfig",
]
