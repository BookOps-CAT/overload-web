"""Pydantic models for request validation and response serialization.

These models wrap dataclasses from shared schemas when possible in order
to enable compatibility with pydantic while minimizing amount of repeated code.
"""

from __future__ import annotations

from inspect import Parameter, Signature

from fastapi import Form
from pydantic import BaseModel, field_validator

from overload_web.shared import schemas


def from_form(model_class: BaseModel):
    """
    A generic function used to create an object from an html form.
    HTML forms can only take data as strings so this class method is
    needed in order to parse the data into the correct types.
    """
    form_fields = []
    for field_name, model_field in model_class.model_fields.items():
        annotation = model_field.annotation
        default = Form(...) if model_field.is_required() else Form(default=None)
        form_fields.append((field_name, annotation, default))

    def func(**data):
        return model_class(**data)

    params = [
        Parameter(
            name,
            Parameter.POSITIONAL_OR_KEYWORD,
            default=default,
            annotation=annotation,
        )
        for name, annotation, default in form_fields
    ]
    func.__signature__ = Signature(parameters=params)  # type: ignore[attr-defined]
    return func


class MatchpointSchema(BaseModel, schemas._Matchpoints):
    """Pydantic model for serializing/deserializing matchpoints from order templates"""


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
