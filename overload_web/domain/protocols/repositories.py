"""
Classes representing a relational database within the domain.

Protocols:

`SqlRepositoryProtocol`
    Defines expected methods for a repository.
"""

from __future__ import annotations

import logging
from typing import Optional, Protocol, Sequence, TypeVar, runtime_checkable

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

    def get(self, id: str) -> Optional[T]: ...  # pragma: no branch

    def list(
        self, offset: Optional[int] = 0, limit: Optional[int] = 0
    ) -> Sequence[T]: ...  # pragma: no branch

    def save(self, obj: T) -> None: ...  # pragma: no branch
