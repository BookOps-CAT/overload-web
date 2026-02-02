"""Domain service for parsing bib records from binary MARC data to domain models."""

from __future__ import annotations

import itertools
import logging
from collections import Counter
from typing import (
    Any,
    BinaryIO,
    Iterator,
    Protocol,
    TypeVar,
    runtime_checkable,
)

from overload_web.bib_records.domain_models import bibs
from overload_web.shared.errors import OverloadError

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

    def map_data(self, record: T) -> dict[str, Any]: ...  # pragma: no branch

    """Map MARC record to a domain object representing the record."""


class BibParser:
    """
    Domain service for parsing MARC records to domain objects.

    This service parses `BinaryIO` and `bytes` objects to `DomainBib` objects based
    on a set of rules used to instantiate a `BibMapper` object.
    """

    def __init__(self, mapper: BibMapper) -> None:
        self.mapper = mapper

    def parse(
        self, data: BinaryIO | bytes, vendor: str | None = "UNKNOWN"
    ) -> list[bibs.DomainBib]:
        """
        Parse MARC records into `DomainBib` objects using the injected `BibMapper`

        Args:
            data: MARC data represented in binary format

        Returns:
            a list of `DomainBib` objects mapped using `BibMapper``
        """
        reader = self.mapper.get_reader(data)
        parsed = []

        for record in reader:
            bib_dict = self.mapper.map_data(record)
            if bib_dict["record_type"] in ["acq", "sel"]:
                bib_dict["vendor"] = vendor
            bib = bibs.DomainBib(**bib_dict)
            logger.info(f"Vendor record parsed: {bib}")
            parsed.append(bib)

        return parsed

    def extract_barcodes(self, records: list[bibs.DomainBib]) -> list[str]:
        """Extract all barcodes from a list of `DomainBib` objects"""
        barcodes = list(itertools.chain.from_iterable([i.barcodes for i in records]))
        barcode_counter = Counter(barcodes)
        dupe_barcodes = [i for i, count in barcode_counter.items() if count > 1]
        if dupe_barcodes:
            raise OverloadError(f"Duplicate barcodes found in file: {dupe_barcodes}")
        return barcodes
