"""Overload Web Jinja2Templates for use in all API routers."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)


@lru_cache
def load_constants() -> dict[str, Any]:
    """Load constants for forms used within app from `form_constants.json`."""
    constants = {}
    with open(BASE_DIR / "data/form_constants.json", "r", encoding="utf-8") as fh:
        constants.update(json.load(fh))
    return constants


constants = load_constants()
templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.globals["fixed_fields"] = constants["fixed_fields"]
templates.env.globals["var_fields"] = constants["var_fields"]
templates.env.globals["matchpoints"] = constants["matchpoints"]
templates.env.globals["bib_formats"] = constants["material_form"]
templates.env.globals["context_fields"] = constants["context_fields"]
templates.env.globals["vendors"] = constants["vendors"]
templates.env.globals["wc2sierra_fields"] = constants["wc2sierra_fields"]
templates.env.globals["application"] = "Overload Web"
