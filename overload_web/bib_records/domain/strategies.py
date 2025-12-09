"""Protocols for defining services that retrieve and parse bib records.

This module defines the fetcher used in the infrastructure layer responsible for
finding the duplicate records in Sierra for a `DomainBib` as well as the parser,
vendor identifier, and updater used in the infrastructure layer to convert data
between pymarc/bookops_marc objects and domain objects. Concrete implementations of
these protocols are defined in the infrastructure layer.

Protocols:

`BibFetcher`
    a protocol that defines the any adapter to Sierra that is capable of retrieving
    records based on identifier keys. Matching is based on specific identifiers such
    as OCLC number, ISBN, or Sierra Bib ID.

`BibMapper`
    a protocol that defines an adapter used to convert MARC objects to domain
    objects.

`BibUpdater`
    a protocol that defines an adapter used to update MARC records based on attributes
    of domain objects and rules.
"""

from __future__ import annotations

import logging
from typing import Any, BinaryIO, Optional, Protocol, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

D = TypeVar("D")  # variable for DomainBib type
M = TypeVar("M")  # variable for MatcherResponse type


@runtime_checkable
class BibAttacherStrategy(Protocol[M, D]):
    def attach(self, responses: list[M]) -> list[D]: ...  # pragma: no branch


@runtime_checkable
class BibMatcherStrategy(Protocol[D, M]):
    def match(
        self,
        records: list[D],
        matchpoints: Optional[dict[str, str]] = None,
    ) -> list[M]: ...  # pragma: no branch


@runtime_checkable
class BibParserStrategy(Protocol[D]):
    rules: dict[str, Any]

    def parse(
        self, data: bytes | BinaryIO, library: str
    ) -> list[D]: ...  # pragma: no branch


@runtime_checkable
class BibUpdaterStrategy(Protocol[D]):
    def update(
        self,
        records: D,
        template_data: Optional[dict[str, Any]] = None,
    ) -> list[D]: ...  # pragma: no branch
