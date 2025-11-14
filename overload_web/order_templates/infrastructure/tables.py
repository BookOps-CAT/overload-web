"""Models representing templates for order-level record processing.

Order templates are reusable objects used for applying consistent values to orders. The
attributes of an order template correspond to those available in the `Order` domain
model.

Models:

`_OrderTemplateBase`
    The base data model used to represent an order template and fields that are shared
    by all models within this module.
`OrderTemplate`
    The table model that includes all fields within an order template including fields
    that are only required for the template to be saved to the database.
`OrderTemplateCreate`
    The data model used to create a new order template.
`OrderTemplateUpdate`
    The data model used to update an existing order template.
"""

from __future__ import annotations

import logging
from typing import Annotated

from pydantic import BaseModel, field_validator
from sqlmodel import Field, MetaData, SQLModel

logger = logging.getLogger(__name__)
metadata = MetaData()


class _OrderTemplateBase(SQLModel):
    """
    A reusable template for applying consistent values to orders.

    Attributes:
        name: the name to be associated with the `OrderTemplate` in the database
        agent: the user who created the `OrderTemplate`

    All other fields correspond to those available in the `Order` domain model.

    """

    name: Annotated[str, Field(nullable=False, unique=True, index=True)]
    agent: Annotated[str, Field(nullable=False, index=True)]
    acquisition_type: Annotated[str | None, Field(default=None)]
    blanket_po: Annotated[str | None, Field(default=None)]
    claim_code: Annotated[str | None, Field(default=None)]
    country: Annotated[str | None, Field(default=None)]
    format: Annotated[str | None, Field(default=None)]
    internal_note: Annotated[str | None, Field(default=None)]
    lang: Annotated[str | None, Field(default=None)]
    material_form: Annotated[str | None, Field(default=None)]
    order_code_1: Annotated[str | None, Field(default=None)]
    order_code_2: Annotated[str | None, Field(default=None)]
    order_code_3: Annotated[str | None, Field(default=None)]
    order_code_4: Annotated[str | None, Field(default=None)]
    order_note: Annotated[str | None, Field(default=None)]
    order_type: Annotated[str | None, Field(default=None)]
    receive_action: Annotated[str | None, Field(default=None)]
    selector_note: Annotated[str | None, Field(default=None)]
    vendor_code: Annotated[str | None, Field(default=None)]
    vendor_notes: Annotated[str | None, Field(default=None)]
    vendor_title_no: Annotated[str | None, Field(default=None)]
    primary_matchpoint: Annotated[str, Field(nullable=False)]
    secondary_matchpoint: Annotated[str | None, Field(default=None)]
    tertiary_matchpoint: Annotated[str | None, Field(default=None)]


class OrderTemplate(_OrderTemplateBase, table=True):
    id: Annotated[int, Field(default=None, primary_key=True, index=True)]


class OrderTemplateCreate(_OrderTemplateBase):
    ...

    @field_validator("*", mode="before")
    @classmethod
    def parse_form_fields(cls, value: str) -> str | None:
        if not value or value.strip() == "":
            return None
        else:
            return value.strip()


class OrderTemplateUpdate(SQLModel):
    name: str | None = None
    agent: str | None = None
    primary_matchpoint: str | None = None
    acquisition_type: str | None = None
    blanket_po: str | None = None
    claim_code: str | None = None
    country: str | None = None
    format: str | None = None
    internal_note: str | None = None
    lang: str | None = None
    material_form: str | None = None
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
    secondary_matchpoint: str | None = None
    tertiary_matchpoint: str | None = None


class OrderTemplateSchema(BaseModel):
    """Pydantic model for serializing/deserializing order templates"""

    acquisition_type: str | None = None
    blanket_po: str | None = None
    claim_code: str | None = None
    country: str | None = None
    format: str | None = None
    internal_note: str | None = None
    lang: str | None = None
    material_form: str | None = None
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
