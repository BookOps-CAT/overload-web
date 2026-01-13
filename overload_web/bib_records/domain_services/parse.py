"""Domain service for parsing bib records from binary MARC data to domain models."""

from __future__ import annotations

import logging
from abc import ABC
from typing import (
    Any,
    BinaryIO,
    Generic,
    Iterator,
    Protocol,
    TypeVar,
    runtime_checkable,
)

from overload_web.bib_records.domain_models import bibs

logger = logging.getLogger(__name__)

T = TypeVar("T", contravariant=True)  # variable bookops_marc `Bib` type


@runtime_checkable
class BibMapper(Protocol[T]):
    """
    Protocol for a service that can map binary MARC data to domain objects
    based on a set of rules.

    This abstraction allows the `BibParser` to remain decoupled from any tool
    or library that may be used to read MARC data. Implementations may include
    `pymarc`, `bookops_marc` or other tools.
    """

    rules: dict[str, Any]

    def get_reader(self, data: bytes | BinaryIO) -> Iterator: ...  # pragma: no branch

    """Instantiate an object that can read MARC binary as an iterator."""

    def identify_vendor(self, record: T) -> dict[str, Any]: ...  # pragma: no branch

    """Instantiate an object that can read MARC binary as an iterator."""

    def map_data(self, record: T) -> dict[str, Any]: ...  # pragma: no branch

    """Map MARC record to a domain object representing the record."""


class BibParser(ABC, Generic[T]):
    """
    Domain service for parsing MARC records to domain objects.

    This service parses `BinaryIO` and `bytes` objects to `DomainBib` objects based
    on a set of rules used to instantiate a `BibMapper` object.
    """

    def __init__(self, mapper: BibMapper) -> None:
        self.mapper = mapper

    def _parse_records(self, data: BinaryIO | bytes) -> list[tuple[dict[str, Any], T]]:
        """
        Internal method used to parse MARC records using the injected `BibMapper`.

        Args:
            data: MARC data represented in binary format
        Returns:
            a list of tuples representing the parsed records and containing the mapped
            data as a dictionary with its associated MARC record.
        """
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
            a list of `DomainBib` objects mapped using `BibMapper`
        """
        parsed: list[bibs.DomainBib] = []
        for bib_dict, record in self._parse_records(data):
            logger.info(f"Vendor record parsed: {bib_dict}")
            parsed.append(bibs.DomainBib(**bib_dict))

        return parsed
