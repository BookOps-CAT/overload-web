"""Parse MARC records"""

import logging
from typing import BinaryIO, Literal, overload

from overload_web.bib_records.domain import bibs, marc_protocols

logger = logging.getLogger(__name__)


class BibParser:
    def __init__(self, mapper: marc_protocols.BibMapper) -> None:
        self.mapper = mapper

    def _parse_full_records(self, data: BinaryIO | bytes) -> list[bibs.DomainBib]:
        mapped_bibs = self.mapper.map_full_bibs(data=data)
        return mapped_bibs

    def _parse_order_level_records(
        self, data: BinaryIO | bytes
    ) -> list[bibs.DomainBib]:
        mapped_bibs = self.mapper.map_order_bibs(data)
        return mapped_bibs

    @overload
    def parse(
        self, data: BinaryIO | bytes, record_type: Literal[bibs.RecordType.CATALOGING]
    ) -> list[bibs.DomainBib]: ...  # pragma: no branch

    @overload
    def parse(
        self, data: BinaryIO | bytes, record_type: Literal[bibs.RecordType.SELECTION]
    ) -> list[bibs.DomainBib]: ...  # pragma: no branch

    @overload
    def parse(
        self, data: BinaryIO | bytes, record_type: Literal[bibs.RecordType.ACQUISITIONS]
    ) -> list[bibs.DomainBib]: ...  # pragma: no branch

    def parse(
        self, data: BinaryIO | bytes, record_type: bibs.RecordType
    ) -> list[bibs.DomainBib]:
        match record_type:
            case bibs.RecordType.CATALOGING:
                return self._parse_full_records(data=data)
            case _:
                return self._parse_order_level_records(data=data)
