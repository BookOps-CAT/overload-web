"""Pydantic models for request validation and response serialization.

These models wrap dataclasses from shared schemas when possible in order
to enable compatibility with pydantic while minimizing amount of repeated code.
"""

from __future__ import annotations

import logging
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

from overload_web.shared import schemas

logger = logging.getLogger(__name__)


class MatchpointSchema(BaseModel):
    """Pydantic model for serializing/deserializing matchpoints from order templates"""

    primary_matchpoint: str | None = None
    secondary_matchpoint: str | None = None
    tertiary_matchpoint: str | None = None


class VendorFileModel(BaseModel, schemas._VendorFile):
    """Pydantic model for serializing/deserializing `VendorFile` domain objects."""


class TemplateDataModel(BaseModel, schemas._TemplateData):
    """Pydantic model for serializing/deserializing order template data"""


class TemplatePatchModel(BaseModel, schemas._TemplateBase):
    """
    Pydantic model for serializing/deserializing order template data
    when used to update a template in the database.
    """


class TemplateCreateModel(BaseModel, schemas._TemplateBase):
    """
    Pydantic model for serializing/deserializing order template data
    used when creating a template in the database.
    """

    name: str
    agent: str
    primary_matchpoint: str

    @field_validator("*", mode="before")
    @classmethod
    def parse_form_fields(cls, value: str) -> str | None:
        if not value or value.strip() == "":
            return None
        else:
            return value.strip()


class ProcessingContext(BaseModel):
    record_type: Literal["acq", "cat", "sel"]
    library: Literal["nypl", "bpl"]
    collection: Literal["BL", "RL", ""] | None

    @field_validator("collection", mode="before")
    @classmethod
    def parse_collection(
        cls, value: Literal["BL", "RL"] | None
    ) -> Literal["BL", "RL"] | None:
        if not value:
            return None
        else:
            return value

    @model_validator(mode="after")
    def validate_values(self) -> ProcessingContext:
        if self.library == "nypl" and not self.collection:
            raise ValueError("Collection is required for NYPL records.")
        elif self.library == "bpl" and self.collection:
            raise ValueError("Collection should be `None` for BPL records.")
        return self
