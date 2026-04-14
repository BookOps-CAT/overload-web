"""`FastAPI` application entry point.

Initializes the `FastAPI` app and registers backend and frontend routers.
"""

from __future__ import annotations

import json
import logging
import logging.config
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from typing import Any, AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from overload_web.presentation import deps
from overload_web.presentation.routers import (
    files,
    frontend,
    order_templates,
    pvf,
    reports,
)

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(dotenv_path="debug.env")
logger = logging.getLogger("overload_web")


@lru_cache
def get_log_config() -> dict[str, Any]:
    with open(BASE_DIR / "data/logging_config.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return constants


logging.config.dictConfig(get_log_config())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create and drop database tables on startup/shutdown."""
    logger.info("Starting up Overload...")
    engine = deps.get_engine_with_uri()
    deps.create_db_and_tables(engine)
    yield
    logger.info("Shutting down Overload...")
    engine.dispose()


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


app = FastAPI(lifespan=lifespan)

app.state.templates = get_templates()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(frontend.frontend_router)
app.include_router(files.api_router, prefix="/files")
app.include_router(pvf.api_router, prefix="/pvf")
app.include_router(order_templates.api_router, prefix="/ot")
app.include_router(reports.api_router, prefix="/reports")
