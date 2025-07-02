"""`FastAPI` application entry point.

Initializes the `FastAPI` app and registers backend and frontend routers.
"""

from __future__ import annotations

from fastapi import FastAPI

from overload_web import logging_config
from overload_web.presentation import api, frontend, partials

logging_config.setup_logging()

app = FastAPI()


app.include_router(frontend.frontend_router)
app.include_router(api.api_router)
app.include_router(partials.htmx_router)
