import logging
import os


class Config(object):

    """Base config, uses staging database server."""

    def __init__(self):
        # grab config variables
        self.DEBUG = os.environ.get("DEBUG", False)

        self.DEV = os.environ.get("DEV", True)

        self.TESTING = os.environ.get("TESTING", False)

        self.CSRF_ENABLED = True

        self.SECRET_KEY = os.environ.get("SECRET_KEY", "secret-key")

        self.MONGO_URI = "mongodb://dev:password@127.0.0.1:27017/netwerker"

    @property
    def LOG_LEVEL(self):
        level = os.getenv(
            "LOG_LEVEL", "DEBUG"
        )  # Default to 'INFO' if LOG_LEVEL is not set
        return {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }.get(
            level, logging.INFO
        )  # Default to logging.INFO if level is not a valid log level
