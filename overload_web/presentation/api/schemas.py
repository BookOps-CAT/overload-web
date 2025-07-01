"""Pydantic models for request validation and response serialization.

These models wrap domain models to enable compatibility with pydantic while
minimizing amount of repeated code. Includes logic for parsing template form data.
"""

from __future__ import annotations

import datetime
from typing import Annotated, Optional, Union

from fastapi import Form
from pydantic import BaseModel, ConfigDict

from overload_web.domain import models


class OrderModel(BaseModel, models.bibs.Order):
    """Pydantic model for serializing/deserializing `Order` domain objects."""

    model_config = ConfigDict(from_attributes=True)


class BibModel(BaseModel, models.bibs.DomainBib):
    """Pydantic model for serializing/deserializing `DomainBib` objects."""

    model_config = ConfigDict(from_attributes=True)


class ContextModel(BaseModel):
    """
    Pydantic model for serializing/deserializing values in
    `SessionContext` objects
    """

    model_config = ConfigDict(from_attributes=True)

    library: models.bibs.LibrarySystem
    collection: models.bibs.Collection
    vendor: Optional[str] = None


class MatchpointsModel(BaseModel, models.templates.Matchpoints):
    """Pydantic model for serializing/deserializing `Matchpoints` domain objects."""

    model_config = ConfigDict(from_attributes=True)


class TemplateModel(BaseModel, models.templates.Template):
    """Pydantic model for serializing/deserializing `Template` domain objects."""

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_form_data(
        cls,
        agent: Annotated[Optional[str], Form()] = None,
        name: Annotated[Optional[str], Form()] = None,
        id: Annotated[Optional[str], Form()] = None,
        blanket_po: Annotated[Optional[str], Form()] = None,
        copies: Annotated[Optional[Union[str, int]], Form()] = None,
        country: Annotated[Optional[str], Form()] = None,
        create_date: Annotated[Optional[Union[datetime.datetime, str]], Form()] = None,
        format: Annotated[Optional[str], Form()] = None,
        fund: Annotated[Optional[str], Form()] = None,
        internal_note: Annotated[Optional[str], Form()] = None,
        lang: Annotated[Optional[str], Form()] = None,
        order_code_1: Annotated[Optional[str], Form()] = None,
        order_code_2: Annotated[Optional[str], Form()] = None,
        order_code_3: Annotated[Optional[str], Form()] = None,
        order_code_4: Annotated[Optional[str], Form()] = None,
        order_type: Annotated[Optional[str], Form()] = None,
        price: Annotated[Optional[Union[str, int]], Form()] = None,
        selector_note: Annotated[Optional[str], Form()] = None,
        status: Annotated[Optional[str], Form()] = None,
        vendor_code: Annotated[Optional[str], Form()] = None,
        var_field_isbn: Annotated[Optional[str], Form()] = None,
        vendor_notes: Annotated[Optional[str], Form()] = None,
        vendor_title_no: Annotated[Optional[str], Form()] = None,
        primary_matchpoint: Annotated[Optional[str], Form()] = None,
        secondary_matchpoint: Annotated[Optional[str], Form()] = None,
        tertiary_matchpoint: Annotated[Optional[str], Form()] = None,
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
                primary=primary_matchpoint,
                secondary=secondary_matchpoint,
                tertiary=tertiary_matchpoint,
            ),
        )


class VendorFileModel(BaseModel, models.files.VendorFile):
    """Pydantic model for serializing/deserializing `VendorFile` domain objects."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
