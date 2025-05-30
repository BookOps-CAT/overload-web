"""
Classes representing a relational database within the domain.

Protocols:

`SqlRepositoryProtocol`
    Defines expected methods for a repository.
"""

from __future__ import annotations

import logging
from typing import Optional, Protocol, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

T = TypeVar("T")
K = TypeVar("K", contravariant=True)


@runtime_checkable
class SqlRepositoryProtocol(Protocol[T, K]):
    """
    Interface for repository operations on generic objects.

    Includes methods for fetching and saving generic objects.
    """

    def get(self, id: K) -> Optional[T]: ...

    def save(self, obj: T) -> None: ...
