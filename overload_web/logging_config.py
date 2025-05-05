"""Creates dictionary to configure logger for Overload"""

import logging
import logging.config
import os

logger = logging.getLogger(__name__)


def create_logger_dict() -> dict:
    """Create a dictionary to configure logger."""
    loggly_token = os.environ.get("LOGGLY_TOKEN")
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "basic": {
                "format": "%(app)s-%(asctime)s-%(filename)s-%(lineno)d-%(levelname)s-%(message)s",  # noqa: E501
                "defaults": {"app": "overload_web"},
            },
            "json": {
                "format": '{"app": "%(name)s", "asciTime": "%(asctime)s", "fileName": "%(name)s", "lineNo":"%(lineno)d", "levelName": "%(levelname)s", "message": "%(message)s"}',  # noqa: E501
            },
        },
        "handlers": {
            "stream": {
                "class": "logging.StreamHandler",
                "formatter": "basic",
                "level": "DEBUG",
            },
            "loggly": {
                "class": "loggly.handlers.HTTPSHandler",
                "formatter": "json",
                "level": "INFO",
                "url": f"https://logs-01.loggly.com/inputs/{loggly_token}/tag/python",
            },
        },
        "loggers": {
            "overload_web": {
                "handlers": ["stream", "loggly"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }


def setup_logging():
    logger_config = create_logger_dict()
    logging.config.dictConfig(logger_config)
