"""Pydantic models for request validation and response serialization.

These models wrap domain models when possible in order to to enable
compatibility with pydantic while minimizing amount of repeated code.
"""

from __future__ import annotations

from typing import Optional

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
    """Pydantic model representing data passed to `SessionContext` objects."""

    library: models.bibs.LibrarySystem
    collection: models.bibs.Collection
    vendor: Optional[str] = None
    record_type: Optional[str] = None

    @classmethod
    def from_form(
        cls,
        library: str = Form(...),
        collection: str = Form(...),
        record_type: str = Form(...),
    ) -> ContextModel:
        return ContextModel(
            library=models.bibs.LibrarySystem(library),
            collection=models.bibs.Collection(collection),
            record_type=record_type,
        )


class MatchpointsModel(BaseModel, models.templates.Matchpoints):
    """Pydantic model for serializing/deserializing `Matchpoints` domain objects."""

    model_config = ConfigDict(from_attributes=True)


class TemplateModel(BaseModel, models.templates.Template):
    """Pydantic model for serializing/deserializing `Template` domain objects."""

    model_config = ConfigDict(from_attributes=True)


class VendorFileModel(BaseModel, models.files.VendorFile):
    """Pydantic model for serializing/deserializing `VendorFile` domain objects."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    @classmethod
    def create(cls, content: bytes, file_name: str | None) -> VendorFileModel:
        """Factory method to enforce ID assignment and domain rules."""
        file_id = models.files.VendorFileId.new()
        file_name = str(file_id) if not file_name else file_name
        return cls(id=file_id, content=content, file_name=file_name)
