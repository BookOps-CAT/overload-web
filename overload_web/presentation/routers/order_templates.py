"""API router for Overload Web order template services."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from overload_web.application.commands.order_template import (
    CreateOrderTemplate,
    GetOrderTemplate,
    ListOrderTemplates,
    UpdateOrderTemplate,
)
from overload_web.presentation import deps, dto

logger = logging.getLogger(__name__)


api_router = APIRouter()


@api_router.post("/template", response_class=HTMLResponse)
def create_template(
    request: Request,
    template: Annotated[Any, Depends(deps.from_form(dto.TemplateCreateModel))],
    repository: Annotated[Any, Depends(deps.order_template_db)],
) -> HTMLResponse:
    """
    Save a new order template to the template database.

    Args:
        template: the order template as an `TemplateCreateModel` object.
        repository: a `repository.OrderTemplateRepository` object

    Returns:
        the saved order template wrapped in a `HTMLResponse` object
    """
    saved_template = CreateOrderTemplate.execute(obj=template, repository=repository)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="forms/template_form.html",
        context={"template": saved_template.__dict__},
    )


@api_router.get("/template", response_class=HTMLResponse)
def get_template(
    request: Request,
    template_id: str,
    repository: Annotated[Any, Depends(deps.order_template_db)],
) -> HTMLResponse:
    """
    Retrieve an order template from the database.

    Args:
        template_id: the template's ID as a string.
        repository: a `repository.OrderTemplateRepository` object

    Returns:
        the retrieved order template wrapped in a `HTMLResponse` object
    """
    template = GetOrderTemplate.execute(template_id=template_id, repository=repository)
    template_out = {k: v for k, v in template.__dict__.items() if v} if template else {}
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="order_templates/rendered.html",
        context={"template": template_out},
    )


@api_router.get("/templates", response_class=HTMLResponse)
def get_template_list(
    request: Request,
    repository: Annotated[Any, Depends(deps.order_template_db)],
    offset: int = 0,
    limit: int = 20,
) -> HTMLResponse:
    """
    List order templates in the database.

    Args:
        repository: a `repository.OrderTemplateRepository` object
        offset: the first template to be listed
        limit: the maximum number of templates to list

    Returns:
        a list of order templates retrieved from the database wrapped in a
        `HTMLResponse` object
    """
    template_list = ListOrderTemplates.execute(
        repository=repository, offset=offset, limit=limit
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="order_templates/template_list.html",
        context={"templates": template_list},
    )


@api_router.patch("/template", response_class=HTMLResponse)
def update_template(
    request: Request,
    template_id: Annotated[str, Form(...)],
    template_patch: Annotated[Any, Depends(deps.from_form(dto.TemplatePatchModel))],
    repository: Annotated[Any, Depends(deps.order_template_db)],
) -> HTMLResponse:
    """
    Apply patch updates to an order templates in the database.

    Args:
        repository:
            a `repository.OrderTemplateRepository` object
        template_id:
            the template's ID as a string.
        template_patch:
            data to be updated in the template as an `TemplatePatchModel` object

    Returns:
        the updated order template wrapped in a `HTMLResponse` object
    """
    updated_template = UpdateOrderTemplate.execute(
        repository=repository, template_id=template_id, obj=template_patch
    )
    template_out = (
        {k: v for k, v in updated_template.__dict__.items() if v}
        if updated_template
        else {}
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="forms/template_form.html",
        context={"template": template_out},
    )


@api_router.get("/forms/templates", response_class=HTMLResponse)
def get_template_form(request: Request) -> HTMLResponse:
    """Renders form for creating/editing order templates."""
    return request.app.state.templates.TemplateResponse(
        request=request, name="forms/template_form.html"
    )
