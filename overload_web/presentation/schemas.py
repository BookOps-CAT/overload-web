"""Pydantic models for request validation and response serialization.

These models wrap domain models when possible in order to to enable
compatibility with pydantic while minimizing amount of repeated code.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from overload_web.domain import models


class VendorFileModel(BaseModel, models.files.VendorFile):
    """Pydantic model for serializing/deserializing `VendorFile` domain objects."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    @classmethod
    def create(cls, content: bytes, file_name: str | None) -> VendorFileModel:
        """Factory method to enforce ID assignment and domain rules."""
        file_id = models.files.VendorFileId.new()
        file_name = str(file_id) if not file_name else file_name
        return cls(id=file_id, content=content, file_name=file_name)
