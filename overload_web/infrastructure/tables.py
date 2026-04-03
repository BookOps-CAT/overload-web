"""Models representing templates for order-level record processing.

Order templates are reusable objects used for applying consistent values to orders. The
attributes of an order template correspond to those available in the `Order` domain
model.

Models:

`_TemplateTableBase`
    The base data model used to represent an order template and fields that are shared
    by all models within this module.
`TemplateTable`
    The table model that includes all fields within an order template including fields
    that are only required for the template to be saved to the database.
"""

from __future__ import annotations

import logging

from sqlmodel import Field, SQLModel

logger = logging.getLogger(__name__)


class _TemplateTableBase(SQLModel):
    """
    A reusable template for applying consistent values to orders.

    Attributes:
        name: the name to be associated with the `TemplateTable` in the database
        agent: the user who created the `TemplateTable`

    All other fields correspond to those available in the `Order` domain model.

    """

    name: str = Field(nullable=False, unique=True, index=True)
    agent: str = Field(nullable=False, index=True)
    acquisition_type: str | None = Field(default=None)
    blanket_po: str | None = Field(default=None)
    claim_code: str | None = Field(default=None)
    country: str | None = Field(default=None)
    format: str | None = Field(default=None)
    internal_note: str | None = Field(default=None)
    lang: str | None = Field(default=None)
    material_form: str | None = Field(default=None)
    order_code_1: str | None = Field(default=None)
    order_code_2: str | None = Field(default=None)
    order_code_3: str | None = Field(default=None)
    order_code_4: str | None = Field(default=None)
    order_note: str | None = Field(default=None)
    order_type: str | None = Field(default=None)
    receive_action: str | None = Field(default=None)
    selector_note: str | None = Field(default=None)
    vendor_code: str | None = Field(default=None)
    vendor_notes: str | None = Field(default=None)
    vendor_title_no: str | None = Field(default=None)
    primary_matchpoint: str = Field(nullable=False)
    secondary_matchpoint: str | None = Field(default=None)
    tertiary_matchpoint: str | None = Field(default=None)


class TemplateTable(_TemplateTableBase, table=True):
    """
    A table model representing order templates including all fields required
    for persistence (i.e., all fields present in a `_TemplateTableBase` object
    with the addition of the unique identifier).
    """

    id: int = Field(default=None, primary_key=True, index=True)
