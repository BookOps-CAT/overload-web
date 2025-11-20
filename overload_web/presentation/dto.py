"""Pydantic models for request validation and response serialization.

These models wrap dataclasses from shared schemas when possible in order
to enable compatibility with pydantic while minimizing amount of repeated code.
"""

from __future__ import annotations

from pydantic import BaseModel, field_validator

from overload_web.shared import schemas


class MatchpointSchema(BaseModel, schemas._Matchpoints):
    """Pydantic model for serializing/deserializing matchpoints from order templates"""


class VendorFileModel(BaseModel, schemas._VendorFile):
    """Pydantic model for serializing/deserializing `VendorFile` domain objects."""


class TemplateDataModel(BaseModel, schemas._TemplateData):
    """Pydantic model for serializing/deserializing order template data"""


class TemplatePatchModel(BaseModel, schemas._TemplateBase):
    """
    Pydantic model for serializing/deserializing order template data
    when used to update a template in the DB.
    """


class TemplateCreateModel(BaseModel, schemas._TemplateBase):
    """
    Pydantic model for serializing/deserializing order template data
    used when creating a template in the DB.
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
