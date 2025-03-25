from fastapi import FastAPI

from overload_web.api import overload_api
from overload_web.frontend import jinja_frontend

app = FastAPI()


app.include_router(jinja_frontend.frontend_router)
app.include_router(overload_api.api_router)
