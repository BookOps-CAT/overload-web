"""Protocols defining ports used in domain services."""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class OCLCBibFetcher(Protocol):
    """Interface for interactions with OCLC Metadata/Search APIs."""

    def get_brief_bibs_by_id(
        self, params: dict[str, Any]
    ) -> list[dict[str, Any]]: ...  # pragma: no branch

    """Search for brief bib resource using specified parameters."""

    def get_full_bib_by_id(self, value: str | int) -> bytes: ...  # pragma: no branch

    """Retrieve for full MARC record as a bytes object for a given ID."""

    def get_full_bib_json_by_id(
        self, value: str
    ) -> dict[str, Any]: ...  # pragma: no branch

    """Retrieve for full MARC record as a json object for a given ID."""
