"""Adapter for reading MARC files and converting into domain objects"""

from __future__ import annotations

import io
from typing import BinaryIO

from bookops_marc import SierraBibReader

from overload_web.application.dto import bib_dto
from overload_web.domain.models import bibs


class BookopsMarcTransformer:
    def __init__(self, library: bibs.LibrarySystem) -> None:
        self.library = library

    def parse(self, data: BinaryIO) -> list[bib_dto.BibDTO]:
        records = []
        reader = SierraBibReader(
            data, library=str(self.library), hide_utf8_warnings=True
        )
        for record in reader:
            obj = bib_dto.BibDTO(
                bib=record, domain_bib=bibs.DomainBib.from_marc(record)
            )
            records.append(obj)
        return records

    def serialize(self, records: list[bib_dto.BibDTO]) -> BinaryIO:
        io_data = io.BytesIO()
        for bib in records:
            io_data.write(bib.bib.as_marc())
        io_data.seek(0)
        return io_data
