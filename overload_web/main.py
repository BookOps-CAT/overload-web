"""`FastAPI` application entry point.

Initializes the `FastAPI` app and registers backend and frontend routers.
"""

from __future__ import annotations

import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from overload_web import config
from overload_web.presentation import api, frontend, partials

load_dotenv(dotenv_path="debug.env")
logger = logging.getLogger("overload_web")


config.setup_logging()

app = FastAPI()

app.state.templates = config.get_templates()
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(frontend.frontend_router)
app.include_router(api.api_router)
app.include_router(partials.htmx_router)
