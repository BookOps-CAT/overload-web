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
from typing import Any, Protocol, Sequence, TypeVar, runtime_checkable

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


@runtime_checkable
class SqlRepositoryProtocol(Protocol[T]):
    """
    Interface for repository operations on generic objects.

    Includes methods for fetching and saving generic objects.
    """

    session: Any

    def get(self, id: str) -> T | None: ...  # pragma: no branch

    def list(
        self, offset: int | None = 0, limit: int | None = 0
    ) -> Sequence[T]: ...  # pragma: no branch

    def save(self, obj: T) -> T: ...  # pragma: no branch

    def update(self, id: str, data: T) -> T | None: ...  # pragma: no branch
