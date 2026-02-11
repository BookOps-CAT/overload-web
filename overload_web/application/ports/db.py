"""Port used to define a database for order templates.

Protocols:

`SqlRepositoryProtocol`
    Defines expected methods for a repository.

"""

from __future__ import annotations

import logging
from typing import Any, Protocol, Sequence, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

T = TypeVar("T")


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

    def apply_updates(self, id: str, data: T) -> T | None: ...  # pragma: no branch
