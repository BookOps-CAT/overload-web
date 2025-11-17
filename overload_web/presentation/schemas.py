"""Pydantic models for request validation and response serialization.

These models wrap domain models when possible in order to to enable
compatibility with pydantic while minimizing amount of repeated code.
"""

from __future__ import annotations

from typing import TypeAlias

from pydantic import BaseModel

from overload_web.files.infrastructure import file_models
from overload_web.order_templates.infrastructure import tables

BaseModelAlias: TypeAlias = BaseModel
VendorFileType: TypeAlias = file_models.VendorFileModel
OrderTemplateSchemaType: TypeAlias = tables.OrderTemplateSchema
OrderTemplateCreateType: TypeAlias = tables.OrderTemplateCreate
OrderTemplateUpdateType: TypeAlias = tables.OrderTemplateUpdate


class MatchpointSchema(BaseModel):
    """Pydantic model for serializing/deserializing matchpoints from order templates"""

    primary_matchpoint: str | None = None
    secondary_matchpoint: str | None = None
    tertiary_matchpoint: str | None = None
