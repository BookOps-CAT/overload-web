"""Domain service for parsing bib records."""

from __future__ import annotations

import itertools
import logging
from abc import ABC
from typing import Any, BinaryIO

from overload_web.bib_records.domain import bibs, marc_protocols

logger = logging.getLogger(__name__)


class BaseBibParser(ABC):
    def __init__(self, mapper: marc_protocols.BibMapper) -> None:
        self.mapper = mapper

    def _parse_records(self, data: BinaryIO | bytes) -> list[tuple[dict, Any]]:
        reader = self.mapper.get_reader(data)
        parsed = []

        for record in reader:
            bib_dict = self.mapper.map_data(record)
            parsed.append((bib_dict, record))

        return parsed


class FullLevelBibParser(BaseBibParser):
    def parse(self, data: BinaryIO | bytes) -> tuple[list[bibs.DomainBib], list[str]]:
        """
        Method used to build `DomainBib` objects for full-level MARC records

        Args:
            data: MARC data represented in binary format

        Returns:
            a list of `bibs.DomainBib` objects mapped using `BibMapper``
        """
        parsed: list[bibs.DomainBib] = []

        for bib_dict, record in self._parse_records(data):
            vendor_info = self.mapper.identify_vendor(record)
            bib_dict["vendor_info"] = bibs.VendorInfo(**vendor_info)
            logger.info(f"Vendor record parsed: {bib_dict}")
            parsed.append(bibs.DomainBib(**bib_dict))
        barcodes = [i.barcodes for i in parsed]
        return (parsed, list(itertools.chain.from_iterable(barcodes)))


class OrderLevelBibParser(BaseBibParser):
    def parse(self, data: BinaryIO | bytes) -> list[bibs.DomainBib]:
        """
        Method used to build `DomainBib` objects for order-level MARC records

        Args:
            data: MARC data represented in binary format

        Returns:
            a list of `bibs.DomainBib` objects mapped using `BibMapper``
        """
        parsed: list[bibs.DomainBib] = []

        for bib_dict, record in self._parse_records(data):
            logger.info(f"Vendor record parsed: {bib_dict}")
            parsed.append(bibs.DomainBib(**bib_dict))

        return parsed
