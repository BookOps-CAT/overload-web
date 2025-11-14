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


# class OrderTemplateSchema(BaseModel):
#     """Pydantic model for serializing/deserializing order templates"""

#     acquisition_type: str | None = None
#     blanket_po: str | None = None
#     claim_code: str | None = None
#     country: str | None = None
#     format: str | None = None
#     internal_note: str | None = None
#     lang: str | None = None
#     material_form: str | None = None
#     order_code_1: str | None = None
#     order_code_2: str | None = None
#     order_code_3: str | None = None
#     order_code_4: str | None = None
#     order_note: str | None = None
#     order_type: str | None = None
#     receive_action: str | None = None
#     selector_note: str | None = None
#     vendor_code: str | None = None
#     vendor_notes: str | None = None
#     vendor_title_no: str | None = None
