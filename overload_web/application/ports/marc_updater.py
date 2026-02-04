from __future__ import annotations

import logging
from typing import Any, Protocol, TypeVar, runtime_checkable

from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)

T = TypeVar("T", covariant=True)  # variable bookops_marc `Bib` type


@runtime_checkable
class MarcUpdaterPort(Protocol[T]):
    """Port defining what the application expects from a MARC updater."""

    def apply_updates(
        self, record: bibs.DomainBib, *, template_data: dict[str, Any] | None = None
    ) -> None:
        """Update a MARC record according to rules and record type."""
        ...
