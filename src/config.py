import logging

class BaseConfig:
    """Base configuration with default settings."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = logging.INFO


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
