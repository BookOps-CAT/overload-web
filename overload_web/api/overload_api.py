from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from overload_web import config, constants
from overload_web.api import schemas
from overload_web.domain import model
from overload_web.services import handlers

api_router = APIRouter()
templates = Jinja2Templates(directory="overload_web/frontend/templates")

CONTEXT: Dict[str, Any] = {
    "application": constants.APPLICATION,
    "fixed_fields": constants.TEMPLATE_FIXED_FIELDS,
    "variable_fields": constants.TEMPLATE_VAR_FIELDS,
    "matchpoints": constants.MATCHPOINTS,
}


@api_router.get("/", response_class=HTMLResponse)
def root(request: Request, page_title: str = "Overload Web"):
    CONTEXT.update({"page_title": page_title})
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context=CONTEXT,
    )


@api_router.get("/vendor_file")
def vendor_file_page(request: Request, page_title: str = "Process Vendor File"):
    CONTEXT.update({"page_title": page_title})
    return templates.TemplateResponse(request=request, name="pvf.html", context=CONTEXT)


@api_router.post("/vendor_file")
def vendor_file_process(
    request: Request,
    order: Annotated[schemas.OrderModel, Depends(schemas.get_order_file)],
    template: Annotated[schemas.OrderTemplateModel, Depends(schemas.get_template)],
    page_title: str = "Process Vendor File Output",
):
    processed_bib = handlers.process_file(
        sierra_service=config.get_sierra_service(library=order.library),
        order_data=model.Order(**order.model_dump()),
        template=model.OrderTemplate(**template.model_dump()),
    )
    CONTEXT.update(
        {
            "page_title": page_title,
            "template": template,
            "order": order,
            "bib": processed_bib,
        }
    )
    return templates.TemplateResponse(request=request, name="pvf.html", context=CONTEXT)
