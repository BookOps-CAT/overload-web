"""Parse MARC records"""

import logging
from typing import BinaryIO

from overload_web.bib_records.domain import bibs, marc_protocols

logger = logging.getLogger(__name__)


class BibParser:
    def __init__(self, mapper: marc_protocols.BibMapper) -> None:
        self.mapper = mapper

    def parse(self, data: BinaryIO | bytes) -> list[bibs.DomainBib]:
        return self.mapper.map_bibs(data)
