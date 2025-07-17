"""Parser for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import copy
import datetime
import io
import json
from functools import lru_cache
from typing import Any, BinaryIO

from bookops_marc import SierraBibReader
from pymarc import Field, Indicators, Subfield

from overload_web.application import dto
from overload_web.domain import models, protocols


@lru_cache
def load_marc_rules() -> dict[str, dict[str, str]]:
    with open("overload_web/presentation/constants.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return constants["marc_mapping"]


class BookopsMarcParser(protocols.bibs.MarcParser[dto.bib.BibDTO]):
    """Parses and serializes MARC records."""

    def __init__(self, library: models.bibs.LibrarySystem) -> None:
        """
        Initialize `BookopsMarcParser` for a specific library.

        Args:
            library: library whose records are being parsed as a `LibrarySystem` obj
        """
        self.library = library
        self.marc_rules = load_marc_rules()

    def _map_order_data(self, order: models.bibs.Order) -> dict:
        """
        Transform an `Order` domain object into MARC field mappings.

        Args:
            order: an `Order` domain object

        Returns:
            a dictionary mapping MARC tags to subfield-value dictionaries.
        """
        out = {}
        for tag in ["960", "961"]:
            tag_dict = {}
            for k, v in self.marc_rules[tag].items():
                tag_dict[k] = getattr(order, v)
            out[tag] = tag_dict
        return out

    def parse(self, data: BinaryIO | bytes) -> list[dto.bib.BibDTO]:
        """
        Parse binary MARC data into a list of `BibDTO` objects.

        Args:
            data: MARC records as file-like object or byte stream.

        Returns:
            a list of `BibDTO` objects containing `bookops_marc.Bib` objects
            and `DomainBib` objects.
        """
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
        """
        Serialize a list of `BibDTO` objects into a binary MARC stream.

        Args:
            records: a list of records as `BibDTO` objects

        Returns:
            MARC binary as an an in-memory file stream.
        """
        io_data = io.BytesIO()
        for record in records:
            io_data.write(record.bib.as_marc())
        io_data.seek(0)
        return io_data

    def update_fields(
        self, record: dto.bib.BibDTO, fields: list[dict[str, Any]]
    ) -> dto.bib.BibDTO:
        """
        Update a `BibDTO` object's `Bib` attribute with new fields and order data.

        Args:
            record: `BibDTO` object representing the bibliographic record.
            fields: a list of new MARC fields to insert as dictionaries.

        Returns:
            the updated record as a `BibDTO` object
        """
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
