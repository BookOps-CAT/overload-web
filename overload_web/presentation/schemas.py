"""API router for Overload Web backend MARC file processing services."""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import Form
from pydantic import BaseModel, field_validator, model_validator

logger = logging.getLogger(__name__)


class MatchpointsModel(BaseModel):
    """Pydantic model for serializing/deserializing matchpoints from order templates"""

    primary_matchpoint: str | None = None
    secondary_matchpoint: str | None = None
    tertiary_matchpoint: str | None = None

    @classmethod
    def from_form(
        self,
        primary_matchpoint: str | None = Form(default=None),
        secondary_matchpoint: str | None = Form(default=None),
        tertiary_matchpoint: str | None = Form(default=None),
    ) -> MatchpointsModel:
        """Class method used to create a `MatchpointsModel` object from an html form"""
        return MatchpointsModel(
            primary_matchpoint=primary_matchpoint,
            secondary_matchpoint=secondary_matchpoint,
            tertiary_matchpoint=tertiary_matchpoint,
        )


class ProcessingContext(BaseModel):
    """A model that represents context necessary to determine processing workflow."""

    collection: Literal["BL", "RL", ""] | None
    library: Literal["nypl", "bpl"]
    record_type: Literal["acq", "cat", "sel"]

    @field_validator("collection", mode="before")
    @classmethod
    def parse_collection(
        cls, value: Literal["BL", "RL"] | None
    ) -> Literal["BL", "RL"] | None:
        """Parses value of `collection` param from html forms."""
        if not value:
            return None
        else:
            return value

    @model_validator(mode="after")
    def validate_values(self) -> ProcessingContext:
        """Ensures `collection` is not passed when processing BPL records."""
        if self.library == "nypl" and not self.collection:
            raise ValueError("Collection is required for NYPL records.")
        elif self.library == "bpl" and self.collection:
            raise ValueError("Collection should be `None` for BPL records.")
        return self

    @classmethod
    def from_form(
        self,
        collection: Literal["BL", "RL", ""] | None = Form(None),
        library: Literal["nypl", "bpl"] = Form(...),
        record_type: Literal["acq", "cat", "sel"] = Form(...),
    ) -> ProcessingContext:
        """Class method used to create a `ProcessingContext` object from an html form"""
        return ProcessingContext(
            collection=collection, library=library, record_type=record_type
        )


class TemplateDataModel(BaseModel):
    """Pydantic model for serializing/deserializing order template data
    when it is used in a processing workflow"""

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

    @classmethod
    def from_form(
        self,
        acquisition_type: str | None = Form(default=None),
        blanket_po: str | None = Form(default=None),
        claim_code: str | None = Form(default=None),
        country: str | None = Form(default=None),
        format: str | None = Form(default=None),
        internal_note: str | None = Form(default=None),
        lang: str | None = Form(default=None),
        material_form: str | None = Form(default=None),
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
    ) -> TemplateDataModel:
        """Class method used to create a `TemplateDataModel` object from an html form"""
        return TemplateDataModel(
            acquisition_type=acquisition_type,
            blanket_po=blanket_po,
            claim_code=claim_code,
            country=country,
            format=format,
            internal_note=internal_note,
            lang=lang,
            material_form=material_form,
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
        )


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
