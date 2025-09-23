"""Parser for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import copy
import io
import logging
from typing import Any, BinaryIO

from bookops_marc import Bib, SierraBibReader
from pymarc import Field, Indicators, Subfield

from overload_web.application import dto
from overload_web.domain import models, protocols

logger = logging.getLogger(__name__)


class BookopsMarcParser(protocols.bibs.MarcParser[dto.BibDTO]):
    """Parses and serializes MARC records."""

    def __init__(self, marc_mapping: dict[str, Any]) -> None:
        """
        Initialize `BookopsMarcParser` for a specific library.

        Args:
            library: library whose records are being parsed as a `LibrarySystem` obj
        """
        self.marc_mapping = marc_mapping

    def _map_bib_from_marc(self, bib: Bib) -> models.bibs.DomainBib:
        """
        Factory method used to build a `DomainBib` from a `bookops_marc.Bib` object.

        Args:
            bib: MARC record represented as a `bookops_marc.Bib` object.

        Returns:
            DomainBib: domain object populated with structured order and identifier
            data.
        """
        out: dict[str, Any] = {}

        out["oclc_number"] = list(bib.oclc_nos.values())
        for k, v in self.marc_mapping["bib"].items():
            if isinstance(v, dict):
                out[k] = str(bib.get(v["tag"]))
            else:
                out[k] = getattr(bib, v)
        out["orders"] = []
        for order in bib.orders:
            order_dict = {}
            for k, v in self.marc_mapping["order"].items():
                if isinstance(v, str):
                    order_dict[k] = getattr(order, v)
                else:
                    field = getattr(order, k)
                    for code, attr in v.items():
                        order_dict[attr] = field.get(code) if field else None
            out["orders"].append(models.bibs.Order(**order_dict))
        return models.bibs.DomainBib(**out)

    def parse(self, data: BinaryIO | bytes, library: str) -> list[dto.BibDTO]:
        """
        Parse binary MARC data into a list of `BibDTO` objects.

        Args:
            data: MARC records as file-like object or byte stream.

        Returns:
            a list of `BibDTO` objects containing `bookops_marc.Bib` objects
            and `DomainBib` objects.
        """
        records = []
        reader = SierraBibReader(data, library=library, hide_utf8_warnings=True)
        for record in reader:
            mapped_domain_bib = self._map_bib_from_marc(bib=record)
            logger.info(f"Vendor record parsed: {mapped_domain_bib}")
            records.append(dto.BibDTO(bib=record, domain_bib=mapped_domain_bib))
        return records

    def serialize(self, records: list[dto.BibDTO]) -> BinaryIO:
        """
        Serialize a list of `BibDTO` objects into a binary MARC stream.

        Args:
            records: a list of records as `BibDTO` objects

        Returns:
            MARC binary as an an in-memory file stream.
        """
        io_data = io.BytesIO()
        for record in records:
            logger.info(f"Writing MARC binary for record: {record.domain_bib.__dict__}")
            io_data.write(record.bib.as_marc())
        io_data.seek(0)
        return io_data


class BookopsMarcUpdater(protocols.bibs.MarcUpdater[dto.BibDTO]):
    def __init__(self, order_mapping: dict[str, Any]) -> None:
        """
        rules includes `order_subfield_mapping` which maps attrs of an `Order`
        object to marc fields/subfields
        """
        self.order_mapping = order_mapping

    def _add_bib_fields(
        self, record: dto.BibDTO, fields: list[dict[str, str]]
    ) -> dto.BibDTO:
        bib_rec = copy.deepcopy(record.bib)
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

    def _update_bib_id(self, record: dto.BibDTO) -> dto.BibDTO:
        if not record.domain_bib.bib_id:
            return record
        bib_rec = copy.deepcopy(record.bib)
        bib_rec.remove_fields("907")
        bib_id = f".b{str(record.domain_bib.bib_id).strip('.b')}"
        bib_rec.add_ordered_field(
            Field(
                tag="907",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value=bib_id)],
            )
        )
        record.bib = bib_rec
        return record

    def update_bib_record(
        self, record: dto.BibDTO, vendor_info: models.bibs.VendorInfo
    ) -> dto.BibDTO:
        updated_rec = self._update_bib_id(record=record)
        return self._add_bib_fields(record=updated_rec, fields=vendor_info.bib_fields)

    def update_order_record(self, record: dto.BibDTO) -> dto.BibDTO:
        bib_rec = copy.deepcopy(record.bib)
        for order in record.domain_bib.orders:
            order_data = order.map_to_marc(rules=self.order_mapping)
            for tag in order_data.keys():
                subfields = []
                for k, v in order_data[tag].items():
                    if v is None:
                        continue
                    elif isinstance(v, list):
                        subfields.extend([Subfield(code=k, value=str(i)) for i in v])
                    else:
                        subfields.append(Subfield(code=k, value=str(v)))
                bib_rec.add_field(
                    Field(tag=tag, indicators=Indicators(" ", " "), subfields=subfields)
                )
        record.bib = bib_rec
        return record
