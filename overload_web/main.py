"""Overload Web application entry point for FastAPI."""

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

from overload_web.presentation import (
    files,
    frontend,
    order_templates,
    pvf,
    pvf_deps,
    reports,
    wc2s,
)

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(dotenv_path="debug.env")
logger = logging.getLogger("overload_web")


@lru_cache
def get_log_config() -> dict[str, Any]:
    """Load logger configuration."""
    with open(BASE_DIR / "data/logging_config.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return constants


logging.config.dictConfig(get_log_config())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create and drop database tables on startup/shutdown."""
    logger.info("Starting up Overload...")
    uri = pvf_deps.get_uri_for_engine()
    engine = pvf_deps.get_engine(uri)
    app.state.engine = engine
    pvf_deps.create_db_and_tables(engine)
    yield
    logger.info("Shutting down Overload...")
    engine.dispose()


app = FastAPI(lifespan=lifespan)


app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(frontend.frontend_router)
app.include_router(files.api_router, prefix="/files")
app.include_router(pvf.api_router, prefix="/pvf")
app.include_router(order_templates.api_router, prefix="/ot")
app.include_router(reports.api_router, prefix="/reports")
app.include_router(wc2s.api_router, prefix="/wc2s")
