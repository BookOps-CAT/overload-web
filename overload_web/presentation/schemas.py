"""Pydantic models for request validation and response serialization.

These models wrap domain models when possible in order to to enable
compatibility with pydantic while minimizing amount of repeated code.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Form
from pydantic import BaseModel, ConfigDict, model_serializer

from overload_web.domain import models


class MatchpointSchema(BaseModel):
    """Pydantic model for serializing/deserializing matchpoints from order templates"""

    primary_matchpoint: str | None = None
    secondary_matchpoint: str | None = None
    tertiary_matchpoint: str | None = None

    @model_serializer
    def as_list(self) -> list[str]:
        return [
            i
            for i in [
                self.primary_matchpoint,
                self.secondary_matchpoint,
                self.tertiary_matchpoint,
            ]
            if i is not None
        ]

    @classmethod
    def from_form(
        cls,
        primary_matchpoint: Annotated[str | None, Form()] = None,
        secondary_matchpoint: Annotated[str | None, Form()] = None,
        tertiary_matchpoint: Annotated[str | None, Form()] = None,
    ) -> MatchpointSchema:
        return MatchpointSchema(
            primary_matchpoint=primary_matchpoint,
            secondary_matchpoint=secondary_matchpoint,
            tertiary_matchpoint=tertiary_matchpoint,
        )


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

    @classmethod
    def from_form(
        cls,
        acquisition_type: Annotated[str | None, Form()] = None,
        blanket_po: Annotated[str | None, Form()] = None,
        claim_code: Annotated[str | None, Form()] = None,
        country: Annotated[str | None, Form()] = None,
        format: Annotated[str | None, Form()] = None,
        internal_note: Annotated[str | None, Form()] = None,
        lang: Annotated[str | None, Form()] = None,
        material_form: Annotated[str | None, Form()] = None,
        order_code_1: Annotated[str | None, Form()] = None,
        order_code_2: Annotated[str | None, Form()] = None,
        order_code_3: Annotated[str | None, Form()] = None,
        order_code_4: Annotated[str | None, Form()] = None,
        order_note: Annotated[str | None, Form()] = None,
        order_type: Annotated[str | None, Form()] = None,
        receive_action: Annotated[str | None, Form()] = None,
        selector_note: Annotated[str | None, Form()] = None,
        vendor_code: Annotated[str | None, Form()] = None,
        vendor_notes: Annotated[str | None, Form()] = None,
        vendor_title_no: Annotated[str | None, Form()] = None,
    ) -> OrderTemplateSchema:
        return OrderTemplateSchema(
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


class VendorFileModel(BaseModel, models.files.VendorFile):
    """Pydantic model for serializing/deserializing `VendorFile` domain objects."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    @classmethod
    def create(cls, content: bytes, file_name: str | None) -> VendorFileModel:
        """Factory method to enforce ID assignment and domain rules."""
        file_id = models.files.VendorFileId.new()
        file_name = str(file_id) if not file_name else file_name
        return cls(id=file_id, content=content, file_name=file_name)
