"""API router for Overload Web order template services."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from overload_web.application.commands.order_template import (
    CreateOrderTemplate,
    GetOrderTemplate,
    ListOrderTemplates,
    UpdateOrderTemplate,
)
from overload_web.presentation import deps

logger = logging.getLogger(__name__)


class TemplatePatchModel(BaseModel):
    """
    Pydantic model for serializing/deserializing data used to update
    an order template in the database.
    """

    acquisition_type: str | None = None
    agent: str | None = None
    blanket_po: str | None = None
    claim_code: str | None = None
    country: str | None = None
    format: str | None = None
    internal_note: str | None = None
    lang: str | None = None
    material_form: str | None = None
    name: str | None = None
    order_code_1: str | None = None
    order_code_2: str | None = None
    order_code_3: str | None = None
    order_code_4: str | None = None
    order_note: str | None = None
    order_type: str | None = None
    receive_action: str | None = None
    selector_note: str | None = None
    vendor_code: str | None = None
    vendor_notes: str | None = None
    vendor_title_no: str | None = None

    primary_matchpoint: str | None = None
    secondary_matchpoint: str | None = None
    tertiary_matchpoint: str | None = None

    @classmethod
    def from_form(
        self,
        acquisition_type: str | None = Form(default=None),
        agent: str | None = Form(default=None),
        blanket_po: str | None = Form(default=None),
        claim_code: str | None = Form(default=None),
        country: str | None = Form(default=None),
        format: str | None = Form(default=None),
        internal_note: str | None = Form(default=None),
        lang: str | None = Form(default=None),
        material_form: str | None = Form(default=None),
        name: str | None = Form(default=None),
        order_code_1: str | None = Form(default=None),
        order_code_2: str | None = Form(default=None),
        order_code_3: str | None = Form(default=None),
        order_code_4: str | None = Form(default=None),
        order_note: str | None = Form(default=None),
        order_type: str | None = Form(default=None),
        receive_action: str | None = Form(default=None),
        selector_note: str | None = Form(default=None),
        vendor_code: str | None = Form(default=None),
        vendor_notes: str | None = Form(default=None),
        vendor_title_no: str | None = Form(default=None),
        primary_matchpoint: str | None = Form(default=None),
        secondary_matchpoint: str | None = Form(default=None),
        tertiary_matchpoint: str | None = Form(default=None),
    ) -> TemplatePatchModel:
        """Class model used to create a `TemplatePatchModel` from an html form."""
        return TemplatePatchModel(
            acquisition_type=acquisition_type,
            agent=agent,
            blanket_po=blanket_po,
            claim_code=claim_code,
            country=country,
            format=format,
            internal_note=internal_note,
            lang=lang,
            material_form=material_form,
            name=name,
            order_code_1=order_code_1,
            order_code_2=order_code_2,
            order_code_3=order_code_3,
            order_code_4=order_code_4,
            order_note=order_note,
            order_type=order_type,
            receive_action=receive_action,
            selector_note=selector_note,
            vendor_code=vendor_code,
            vendor_notes=vendor_notes,
            vendor_title_no=vendor_title_no,
            primary_matchpoint=primary_matchpoint,
            secondary_matchpoint=secondary_matchpoint,
            tertiary_matchpoint=tertiary_matchpoint,
        )


class TemplateCreateModel(TemplatePatchModel):
    """
    Pydantic model for serializing/deserializing data used to create
    an order template in the database.

    Inherits `from_from` class method from `TemplatePatchModel` parent class
    which is used when creating a new order template from an html form.
    """

    name: str
    agent: str
    primary_matchpoint: str


api_router = APIRouter()


@api_router.post("/template", response_class=HTMLResponse)
def create_template(
    request: Request,
    template: Annotated[Any, Depends(TemplateCreateModel.from_form)],
    repository: Annotated[Any, Depends(deps.order_template_db)],
) -> HTMLResponse:
    """
    Save a new order template to the template database.

    Args:
        template: the order template as an `TemplateCreateModel` object.
        repository: a `repository.OrderTemplateRepository` object

    Returns:
        the saved order template as a dict wrapped in an `HTMLResponse` object
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
        the retrieved order template as a dict wrapped in an `HTMLResponse` object
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
        a list of order templates retrieved from the database wrapped in an
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
    template_patch: Annotated[Any, Depends(TemplatePatchModel.from_form)],
    repository: Annotated[Any, Depends(deps.order_template_db)],
) -> HTMLResponse:
    """
    Apply patch updates to an order template in the database.

    Args:
        repository:
            a `repository.OrderTemplateRepository` object
        template_id:
            the template's ID as a string.
        template_patch:
            data to be updated in the template as an `TemplatePatchModel` object

    Returns:
        the updated order template as a dict wrapped in an `HTMLResponse` object
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
    """Renders html form used to create/edit order templates."""
    return request.app.state.templates.TemplateResponse(
        request=request, name="forms/template_form.html"
    )
