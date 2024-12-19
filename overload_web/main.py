from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pathlib import Path

from overload_web import services
from overload_web.domain import model
from overload_web import config

app = FastAPI()

BASE_PATH = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=f"{BASE_PATH}/static"), name="static")
templates = Jinja2Templates(directory=f"{BASE_PATH}/templates")


@app.get("/", response_class=HTMLResponse)
def root(request: Request, application: str = "Overload Web"):
    return templates.TemplateResponse(
        request=request, name="home.html", context={"application": application}
    )


@app.get("/about", response_class=HTMLResponse)
def about(request: Request, application: str = "Overload Web"):
    return templates.TemplateResponse(
        request=request, name="about.html", context={"application": application}
    )


@app.get("/vendor_file", response_class=HTMLResponse)
def process_vendor_file(request: Request):
    return templates.TemplateResponse(request=request, name="base.html")


@app.get("/match")
def match_endpoint(order: model.Order, matchpoints: list[str], library: str):
    session_adapter = config.get_session_adapter(library=library)
    matched_bibs = services.match(
        order_data=order, sierra_service=session_adapter, matchpoints=matchpoints
    )
    return {"matched_bibs": matched_bibs}
