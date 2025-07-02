"""`FastAPI` application entry point.

Initializes the `FastAPI` app and registers backend and frontend routers.
"""

from __future__ import annotations

from fastapi import FastAPI

from overload_web import logging_config
from overload_web.presentation import jinja_frontend, overload_api

logging_config.setup_logging()

app = FastAPI()


app.include_router(jinja_frontend.frontend_router)
app.include_router(overload_api.api_router)
