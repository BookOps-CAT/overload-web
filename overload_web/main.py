"""`FastAPI` application entry point.

Initializes the `FastAPI` app and registers backend and frontend routers.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from overload_web import config
from overload_web.presentation import api, deps, frontend, partials

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(dotenv_path="debug.env")
logger = logging.getLogger("overload_web")


config.setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create and drop database tables on startup/shutdown."""
    logger.info("Starting up Overload...")
    engine = deps.get_engine_with_uri()
    deps.create_db_and_tables(engine)
    yield
    logger.info("Shutting down Overload...")
    engine.dispose()


app = FastAPI(lifespan=lifespan)

app.state.templates = config.get_templates()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(frontend.frontend_router)
app.include_router(api.api_router, prefix="/api")
app.include_router(partials.htmx_router, prefix="/htmx")
