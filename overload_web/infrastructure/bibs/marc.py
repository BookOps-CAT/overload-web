"""Adapter for reading MARC files and converting into domain objects"""

from __future__ import annotations

import io
from typing import BinaryIO

from bookops_marc import SierraBibReader

from overload_web.application import dto
from overload_web.domain import models


class BookopsMarcTransformer:
    def __init__(self, library: models.bibs.LibrarySystem) -> None:
        self.library = library

    def parse(self, data: BinaryIO) -> list[dto.bib.BibDTO]:
        records = []
        reader = SierraBibReader(
            data, library=str(self.library), hide_utf8_warnings=True
        )
        for record in reader:
            obj = dto.bib.BibDTO(
                bib=record, domain_bib=models.bibs.DomainBib.from_marc(record)
            )
            records.append(obj)
        return records

    def serialize(self, records: list[dto.bib.BibDTO]) -> BinaryIO:
        io_data = io.BytesIO()
        for record in records:
            io_data.write(record.bib.as_marc())
        io_data.seek(0)
        return io_data

    # @classmethod
    # def for_library(cls, library: str) -> BookopsMarcTransformer:
    #     return cls()
