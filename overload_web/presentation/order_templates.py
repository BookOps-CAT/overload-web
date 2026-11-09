"""API router for Overload Web order template services."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, Response

from overload_web.application.pvf import queries
from overload_web.domain.pvf import commands
from overload_web.presentation import pvf_deps, schemas
from overload_web.presentation.templates import templates

logger = logging.getLogger(__name__)


api_router = APIRouter()


@api_router.post("/template", response_class=Response)
def create_template(
    bus: Annotated[Any, Depends(pvf_deps.get_message_bus)],
    template: Annotated[Any, Depends(schemas.TemplateCreateModel.from_form)],
) -> Response:
    """Save a new order template to the template database.

    Args:
        bus: a `ports.MessageBusPort` object used by the workflow
        template: the order template as an `TemplateCreateModel` object.

    Returns:
        204 response with 'templatesChanged' in headers for htmx trigger.

    """
    bus.send(commands.CreateOrderTemplate(data=template))
    return Response(status_code=204, headers={"HX-Trigger": "templatesChanged"})


@api_router.get("/template", response_class=HTMLResponse)
def get_template(
    request: Request, template_id: str, uow: Annotated[Any, Depends(pvf_deps.get_uow)]
) -> HTMLResponse:
    """Retrieve an order template from the database.

    Args:
        request: the HTTP request sent by the app
        template_id: the template's ID as a string.
        uow: a `ports.UnitOfWorkProtocol` object used by the endpoint.

    Returns:
        the retrieved order template as a dict wrapped in an `HTMLResponse` object

    """
    template = queries.get_order_template(template_id=template_id, uow=uow)
    template_out = {k: v for k, v in template.__dict__.items() if v} if template else {}
    return templates.TemplateResponse(
        request=request,
        name="pvf_partials/template_form.html",
        context={"template": template_out},
    )


@api_router.get("/templates", response_class=HTMLResponse)
def get_template_list(
    request: Request,
    uow: Annotated[Any, Depends(pvf_deps.get_uow)],
    offset: int = 0,
    limit: int = 20,
) -> HTMLResponse:
    """List order templates in the database.

    Args:
        request: the HTTP request sent by the app
        uow: a `ports.UnitOfWorkProtocol` object used by the endpoint.
        offset: the first template to be listed
        limit: the maximum number of templates to list

    Returns:
        a list of order templates retrieved from the database wrapped in an
        `HTMLResponse` object

    """
    template_list = queries.list_order_templates(uow=uow, offset=offset, limit=limit)
    return templates.TemplateResponse(
        request=request,
        name="pvf_partials/template_list.html",
        context={"templates": template_list},
    )


@api_router.patch("/template", response_class=Response)
def update_template(
    bus: Annotated[Any, Depends(pvf_deps.get_message_bus)],
    template_id: Annotated[str, Form(...)],
    template_patch: Annotated[Any, Depends(schemas.TemplateDataModel.from_form)],
) -> Response:
    """Apply patch updates to an order template in the database.

    Args:
        bus:
            a `ports.MessageBusPort` object used by the workflow
        template_id:
            the template's ID as a string.
        template_patch:
            data to be updated in the template as an `TemplateDataModel` object

    Returns:
        204 response with 'templatesChanged' in headers for htmx trigger.

    """
    bus.send(commands.UpdateOrderTemplate(template_id=template_id, data=template_patch))
    return Response(status_code=204, headers={"HX-Trigger": "templatesChanged"})


@api_router.get("/forms/templates", response_class=HTMLResponse)
def get_template_form(request: Request) -> HTMLResponse:
    """Render html form used to create/edit order templates."""
    return templates.TemplateResponse(
        request=request, name="pvf_partials/template_form.html"
    )
