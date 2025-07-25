"""Pydantic models for request validation and response serialization.

These models wrap domain models when possible in order to to enable
compatibility with pydantic while minimizing amount of repeated code.
"""

from __future__ import annotations

import datetime
from typing import Annotated

from fastapi import Form
from pydantic import BaseModel, ConfigDict, field_serializer

from overload_web.domain import models


class MatchpointsModel(BaseModel, models.templates.Matchpoints):
    """Pydantic model for serializing/deserializing `Matchpoints` domain objects."""

    model_config = ConfigDict(from_attributes=True)


class TemplateModel(BaseModel, models.templates.Template):
    """Pydantic model for serializing/deserializing `Template` domain objects."""

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_form_data(
        cls,
        agent: Annotated[str | None, Form()] = None,
        name: Annotated[str | None, Form()] = None,
        id: Annotated[str | None, Form()] = None,
        blanket_po: Annotated[str | None, Form()] = None,
        copies: Annotated[str | int | None, Form()] = None,
        country: Annotated[str | None, Form()] = None,
        create_date: Annotated[datetime.datetime | str | None, Form()] = None,
        format: Annotated[str | None, Form()] = None,
        fund: Annotated[str | None, Form()] = None,
        internal_note: Annotated[str | None, Form()] = None,
        lang: Annotated[str | None, Form()] = None,
        order_code_1: Annotated[str | None, Form()] = None,
        order_code_2: Annotated[str | None, Form()] = None,
        order_code_3: Annotated[str | None, Form()] = None,
        order_code_4: Annotated[str | None, Form()] = None,
        order_type: Annotated[str | None, Form()] = None,
        price: Annotated[str | int | None, Form()] = None,
        selector_note: Annotated[str | None, Form()] = None,
        status: Annotated[str | None, Form()] = None,
        vendor_code: Annotated[str | None, Form()] = None,
        var_field_isbn: Annotated[str | None, Form()] = None,
        vendor_notes: Annotated[str | None, Form()] = None,
        vendor_title_no: Annotated[str | None, Form()] = None,
        primary: Annotated[str | None, Form()] = None,
        secondary: Annotated[str | None, Form()] = None,
        tertiary: Annotated[str | None, Form()] = None,
    ) -> TemplateModel:
        """
        Create a `TemplateModel` instance from multipart/form-data submission.

        This method is used with FastAPI's `Depends()` to extract form fields
        and transform them into a structured model instance, including nested
        matchpoints.

        Returns:
            the populated template as a `TemplateModel` object.
        """
        return TemplateModel(
            create_date=create_date,
            fund=fund,
            vendor_code=vendor_code,
            vendor_title_no=vendor_title_no,
            selector_note=selector_note,
            order_type=order_type,
            price=price,
            status=status,
            internal_note=internal_note,
            var_field_isbn=var_field_isbn,
            vendor_notes=vendor_notes,
            copies=copies,
            format=format,
            lang=lang,
            country=country,
            blanket_po=blanket_po,
            name=name,
            id=(models.templates.TemplateId(value=id) if id else None),
            agent=agent,
            order_code_1=order_code_1,
            order_code_2=order_code_2,
            order_code_3=order_code_3,
            order_code_4=order_code_4,
            matchpoints=MatchpointsModel(
                primary=primary,
                secondary=secondary,
                tertiary=tertiary,
            ),
        )

    @field_serializer("matchpoints")
    def serialize_matchpoints(self, matchpoints: models.templates.Matchpoints) -> dict:
        return {k: v for k, v in matchpoints.__dict__.items() if v}


class VendorFileModel(BaseModel, models.files.VendorFile):
    """Pydantic model for serializing/deserializing `VendorFile` domain objects."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    @classmethod
    def create(cls, content: bytes, file_name: str | None) -> VendorFileModel:
        """Factory method to enforce ID assignment and domain rules."""
        file_id = models.files.VendorFileId.new()
        file_name = str(file_id) if not file_name else file_name
        return cls(id=file_id, content=content, file_name=file_name)
