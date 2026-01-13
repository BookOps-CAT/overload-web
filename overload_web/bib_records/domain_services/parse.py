"""Domain service for parsing bib records."""

from __future__ import annotations

import logging
from abc import ABC
from typing import Any, BinaryIO, Iterator, Protocol, runtime_checkable

from overload_web.bib_records.domain_models import bibs

logger = logging.getLogger(__name__)


@runtime_checkable
class BibMapper(Protocol):
    """
    Protocol for a service that can map domain objects representing bib records
    to MARC based on a set of rules.

    This abstraction allows the `BibParser` to remain decoupled from any tool
    or library that may be used to read MARC data. Implementations may include
    `pymarc`, `bookops_marc` or other tools.
    """

    rules: dict[str, Any]

    def get_reader(self, data: bytes | BinaryIO) -> Iterator: ...  # pragma: no branch

    """Instantiate an object that can read MARC binary as an iterator."""

    def identify_vendor(
        self, record: bibs.DomainBib
    ) -> dict[str, Any]: ...  # pragma: no branch

    """Instantiate an object that can read MARC binary as an iterator."""

    def map_data(
        self, record: bibs.DomainBib
    ) -> dict[str, Any]: ...  # pragma: no branch

    """Map MARC record to a domain object representing the record."""


class BibParser(ABC):
    def __init__(self, mapper: BibMapper) -> None:
        self.mapper = mapper

    def _parse_records(self, data: BinaryIO | bytes) -> list[tuple[dict, Any]]:
        reader = self.mapper.get_reader(data)
        parsed = []

        for record in reader:
            bib_dict = self.mapper.map_data(record)
            parsed.append((bib_dict, record))

        return parsed


class FullLevelBibParser(BibParser):
    def parse(self, data: BinaryIO | bytes) -> list[bibs.DomainBib]:
        """
        Method used to build `DomainBib` objects for full-level MARC records

        Args:
            data: MARC data represented in binary format

        Returns:
            a list of `DomainBib` objects mapped using `BibMapper``
        """
        parsed: list[bibs.DomainBib] = []

        for bib_dict, record in self._parse_records(data):
            vendor_info = self.mapper.identify_vendor(record)
            bib_dict["vendor_info"] = bibs.VendorInfo(**vendor_info)
            logger.info(f"Vendor record parsed: {bib_dict}")
            parsed.append(bibs.DomainBib(**bib_dict))
        return parsed


class OrderLevelBibParser(BibParser):
    def parse(self, data: BinaryIO | bytes) -> list[bibs.DomainBib]:
        """
        Method used to build `DomainBib` objects for order-level MARC records

        Args:
            data: MARC data represented in binary format

        Returns:
            a list of `DomainBib` objects mapped using `BibMapper``
        """
        parsed: list[bibs.DomainBib] = []

        for bib_dict, record in self._parse_records(data):
            logger.info(f"Vendor record parsed: {bib_dict}")
            parsed.append(bibs.DomainBib(**bib_dict))

        return parsed
