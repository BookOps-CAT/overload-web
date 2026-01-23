"""Functions to help configure FastAPI Application"""

import json
import logging
import logging.config
from functools import lru_cache
from pathlib import Path

from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent


def setup_logging():
    """Sets up logging based on logger dict"""
    logger_config = {
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
        },
        "loggers": {
            "overload_web": {
                "handlers": ["stream"],
                "level": "DEBUG",
                "propagate": True,
            },
        },
    }
    logging.config.dictConfig(logger_config)


@lru_cache
def get_templates() -> Jinja2Templates:
    """Loads Jinja2 templates and sets env vars"""
    with open(BASE_DIR / "data/form_constants.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    templates = Jinja2Templates(directory=BASE_DIR / "templates")
    templates.env.globals["fixed_fields"] = constants["fixed_fields"]
    templates.env.globals["var_fields"] = constants["var_fields"]
    templates.env.globals["matchpoints"] = constants["matchpoints"]
    templates.env.globals["bib_formats"] = constants["material_form"]
    templates.env.globals["context_fields"] = constants["context_fields"]
    templates.env.globals["vendors"] = constants["vendors"]
    templates.env.globals["application"] = "Overload Web"
    return templates
