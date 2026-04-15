"""Domain models that define order templates.

Classes:
`OrderTemplateBase`
    Defines a base entity for an order template. This includes all fields required for
    creating or updating an order template.

`OrderTemplate`
    Defines an order template domain entity. This includes all fields required for
    persisting an order template to the database (i.e., all fields present in an
    `OrderTemplateBase` object with the addition of the unique identifier).

"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class OrderTemplateBase:
    """Defines a base entity for an order template"""

    acquisition_type: str | None = None
    agent: str | None = None
    blanket_po: str | None = None
    claim_code: str | None = None
    country: str | None = None
    format: str | None = None
    internal_note: str | None = None
    lang: str | None = None
    material_form: str | None = None
    name: str | None = None
    order_code_1: str | None = None
    order_code_2: str | None = None
    order_code_3: str | None = None
    order_code_4: str | None = None
    order_note: str | None = None
    order_type: str | None = None
    receive_action: str | None = None
    selector_note: str | None = None
    vendor_code: str | None = None
    vendor_notes: str | None = None
    vendor_title_no: str | None = None

    primary_matchpoint: str | None = None
    secondary_matchpoint: str | None = None
    tertiary_matchpoint: str | None = None


@dataclass(kw_only=True)
class OrderTemplate(OrderTemplateBase):
    """Defines an order template domain entity"""

    id: int
