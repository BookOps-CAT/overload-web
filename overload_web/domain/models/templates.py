"""Domain models that define order templates and their associated database.

Classes:
`OrderTemplateBase`
    Defines a base entity for an order template. This includes all fields required for
    creating or updating an order template.

`OrderTemplate`
    Defines an order template domain entity. This includes all fields required for
    persisting an order template to the database (i.e., all fields present in an
    `OrderTemplateBase` object with the addition of the unique identifier).

Protocols:

`SqlRepositoryProtocol`
    Defines expected methods for a repository.

"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TypeVar

from overload_web.shared import schemas

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(kw_only=True)
class OrderTemplateBase(schemas._TemplateBase):
    """Defines a base entity for an order template"""


@dataclass(kw_only=True)
class OrderTemplate(OrderTemplateBase):
    """Defines an order template domain entity"""

    id: int
