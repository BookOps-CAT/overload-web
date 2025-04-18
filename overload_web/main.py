from fastapi import FastAPI

from overload_web.presentation.api import overload_api
from overload_web.presentation.frontend import jinja_frontend

app = FastAPI()


app.include_router(jinja_frontend.frontend_router)
app.include_router(overload_api.api_router)
