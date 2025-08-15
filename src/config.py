import logging
import os

class BaseConfig:
    """Base configuration with default settings."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = logging.INFO

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in {'true', '1', 't'}
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'change-me')
    FRONTEND_BASE_URL = os.environ.get('FRONTEND_BASE_URL', 'http://localhost:5000')


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
