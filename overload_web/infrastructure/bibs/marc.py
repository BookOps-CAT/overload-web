"""Adapter for reading MARC files and converting into domain objects"""

from __future__ import annotations

import copy
import datetime
import io
from typing import Any, BinaryIO

from bookops_marc import SierraBibReader
from pymarc import Field, Indicators, Subfield

from overload_web import constants
from overload_web.application import dto
from overload_web.domain import models


class BookopsMarcTransformer:
    def __init__(self, library: models.bibs.LibrarySystem) -> None:
        self.library = library

    def _map_order_data(self, order: models.bibs.Order) -> dict:
        out = {}
        for tag in ["960", "961"]:
            tag_dict = {}
            for k, v in constants.MARC_MAPPING[tag].items():
                tag_dict[k] = getattr(order, v)
            out[tag] = tag_dict
        return out

    def parse(self, data: BinaryIO) -> list[dto.bib.BibDTO]:
        records = []
        reader = SierraBibReader(
            data, library=str(self.library), hide_utf8_warnings=True
        )
        for record in reader:
            domain_bib = models.bibs.DomainBib.from_marc(record)
            obj = dto.bib.BibDTO(bib=record, domain_bib=domain_bib)
            records.append(obj)
        return records

    def serialize(self, records: list[dto.bib.BibDTO]) -> BinaryIO:
        io_data = io.BytesIO()
        for record in records:
            io_data.write(record.bib.as_marc())
        io_data.seek(0)
        return io_data

    def update_fields(
        self, record: dto.bib.BibDTO, fields: list[dict[str, Any]]
    ) -> dto.bib.BibDTO:
        bib_rec = copy.deepcopy(record.bib)
        if record.domain_bib.bib_id:
            bib_rec.remove_fields("907")
            bib_rec.add_ordered_field(
                Field(
                    tag="907",
                    indicators=Indicators(" ", " "),
                    subfields=[
                        Subfield(
                            code="a",
                            value=f".b{str(record.domain_bib.bib_id).strip('.b')}",
                        )
                    ],
                )
            )
        for order in record.domain_bib.orders:
            order_data = self._map_order_data(order)
            for tag in ["960", "961"]:
                subfields = []
                for k, v in order_data[tag].items():
                    if v is None:
                        continue
                    elif isinstance(v, list):
                        subfields.extend([Subfield(code=k, value=str(i)) for i in v])
                    elif isinstance(v, (datetime.date, datetime.datetime)):
                        date = datetime.datetime.strftime(v, format="%Y-%m-%d")
                        subfields.append(Subfield(code=k, value=date))
                    else:
                        subfields.append(Subfield(code=k, value=str(v)))
                bib_rec.add_field(
                    Field(tag=tag, indicators=Indicators(" ", " "), subfields=subfields)
                )
        for field in fields:
            bib_rec.add_ordered_field(
                Field(
                    tag=field["tag"],
                    indicators=Indicators(field["ind1"], field["ind2"]),
                    subfields=[
                        Subfield(code=field["subfield_code"], value=field["value"])
                    ],
                )
            )
        record.bib = bib_rec
        return record
