from typing import Annotated, Any, Dict, List

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from overload_web import config, constants
from overload_web.adapters import schemas
from overload_web.domain import model
from overload_web.services import handlers

app = FastAPI()
templates = Jinja2Templates(directory="overload_web/templates")

CONTEXT: Dict[str, Any] = {
    "application": constants.APPLICATION,
    "field_constants": constants.FIELD_CONSTANTS,
    "library": None,
    "destination": None,
    "field_constants": constants.FIELD_CONSTANTS,
    "library": None,
    "destination": None,
}


@app.get("/", response_class=HTMLResponse)
def root(request: Request, page_title: str = "Overload Web"):
    CONTEXT.update({"page_title": page_title})
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context=CONTEXT,
    )


@app.post("/", response_class=HTMLResponse)
def update_library_context(
    request: Request,
    library: Annotated[str, Form()],
    destination: Annotated[str, Form()],
    page_title: str = "Overload Web",
):
    CONTEXT.update(
        {"page_title": page_title, "library": library, "destination": destination}
    )
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context=CONTEXT,
    )


@app.get("/vendor_file")
def vendor_file_page(
    request: Request,
    page_title: str = "Process Vendor File",
):
    CONTEXT.update({"page_title": page_title})
    return templates.TemplateResponse(request=request, name="pvf.html", context=CONTEXT)


@app.post("/vendor_file")
def vendor_file_process(
    request: Request,
    marc_file: Annotated[List[schemas.OrderBibModel], Depends(schemas.read_marc_file)],
    template: Annotated[
        schemas.OrderTemplateModel, Depends(schemas.get_template, CONTEXT["library"])
    ],
    page_title: str = "Process Vendor File Output",
):
    if not CONTEXT["library"]:
        raise ValueError("Missing library")
    processed_bibs = []
    for bib in marc_file:
        processed_bibs.append(
            handlers.process_file(
                sierra_service=config.get_sierra_service(library=CONTEXT["library"]),
                order_bib=model.OrderBib(
                    bib_id=bib.bib_id, orders=bib.orders, library=CONTEXT["library"]
                ),
                template=model.OrderTemplate(**template.model_dump()),
            )
        )
    CONTEXT.update(
        {
            "page_title": page_title,
            "template": template,
            "processed_bibs": processed_bibs,
        }
    )
    return templates.TemplateResponse(request=request, name="pvf.html", context=CONTEXT)
