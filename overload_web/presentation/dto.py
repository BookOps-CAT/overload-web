"""Pydantic models for request validation and response serialization.

These models wrap domain models when possible in order to to enable
compatibility with pydantic while minimizing amount of repeated code.
"""

from __future__ import annotations

from typing import TypeAlias

from pydantic import BaseModel, ConfigDict

from overload_web.order_templates.infrastructure import tables
from overload_web.shared import schemas

BaseModelAlias: TypeAlias = BaseModel
OrderTemplateSchemaType: TypeAlias = tables.OrderTemplateSchema
OrderTemplateCreateType: TypeAlias = tables.OrderTemplateCreate
OrderTemplateUpdateType: TypeAlias = tables.OrderTemplateUpdate


class MatchpointSchema(BaseModel, schemas._Matchpoints):
    """Pydantic model for serializing/deserializing matchpoints from order templates"""


class VendorFileModel(BaseModel, schemas._VendorFile):
    """Pydantic model for serializing/deserializing `VendorFile` domain objects."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
