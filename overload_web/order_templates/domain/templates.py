"""Domain models that define order templates"""

from __future__ import annotations

from dataclasses import dataclass

from overload_web.shared import schemas


@dataclass(kw_only=True)
class OrderTemplateBase(schemas._TemplateBase):
    """Defines a base entity for an order template"""


@dataclass(kw_only=True)
class OrderTemplate(OrderTemplateBase):
    """Defines an order template domain entity"""

    id: int
