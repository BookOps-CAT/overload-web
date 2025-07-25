"""
Classes representing a relational database within the domain.

Protocols:

`SqlRepositoryProtocol`
    Defines expected methods for a repository.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol, Sequence, TypeVar, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover
    from sqlmodel import Session

logger = logging.getLogger(__name__)

T = TypeVar("T")


@runtime_checkable
class SqlRepositoryProtocol(Protocol[T]):
    """
    Interface for repository operations on generic objects.

    Includes methods for fetching and saving generic objects.
    """

    session: Session

    def get(self, id: str) -> T | None: ...  # pragma: no branch

    def list(
        self, offset: int | None = 0, limit: int | None = 0
    ) -> Sequence[T]: ...  # pragma: no branch

    def save(self, obj: T) -> None: ...  # pragma: no branch
