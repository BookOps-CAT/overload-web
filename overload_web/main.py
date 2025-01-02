from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from overload_web import services, config, schemas
from overload_web.domain import model


app = FastAPI()
templates = Jinja2Templates(directory="overload_web/templates")


@app.get("/", response_class=HTMLResponse)
def root(
    request: Request,
    application: str = "Overload",
    page_title: str = "Overload Web",
    include_in_schema=False,
):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"application": application, "page_title": page_title},
    )


@app.post("/attach")
def attach_endpoint(order: schemas.OrderModel, bib_ids: List[str]):
    bib = services.attach(order_data=model.Order(**order.model_dump()), bib_ids=bib_ids)
    return {"bib": bib}


@app.get("/vendor_file")
def vendor_file_page(
    request: Request,
    application: str = "Overload",
    page_title: str = "Process Vendor File",
    include_in_schema=False,
):
    return templates.TemplateResponse(
        request=request,
        name="pvf.html",
        context={"application": application, "page_title": page_title},
    )


@app.post("/vendor_file")
def vendor_file_process(
    order: schemas.OrderModel, template: schemas.OrderTemplateModel
):
    processed_bib = services.process_file(
        sierra_service=config.get_sierra_service(library=order.library),
        order_data=model.Order(**order.model_dump()),
        template=model.OrderTemplate(**template.model_dump()),
    )
    return {"bib": processed_bib}
