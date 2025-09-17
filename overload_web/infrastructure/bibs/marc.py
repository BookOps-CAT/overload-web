"""Parser for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import copy
import io
import logging
from typing import Any, BinaryIO

from bookops_marc import Bib, SierraBibReader
from bookops_marc.models import Order as BookopsMarcOrder
from pymarc import Field, Indicators, Subfield

from overload_web.application import dto
from overload_web.domain import models, protocols

logger = logging.getLogger(__name__)


class BookopsMarcParser(protocols.bibs.MarcParser[dto.BibDTO]):
    """Parses and serializes MARC records."""

    MARC_ORDER_MAPPING: dict[str, dict[str, str]] = {
        "907": {"a": "bib_id"},
        "960": {
            "c": "order_code_1",
            "d": "order_code_2",
            "e": "order_code_3",
            "f": "order_code_4",
            "g": "format",
            "i": "order_type",
            "m": "status",
            "o": "copies",
            "q": "create_date",
            "s": "price",
            "t": "locations",
            "u": "fund",
            "v": "vendor_code",
            "w": "lang",
            "x": "country",
            "z": "order_id",
        },
        "961": {
            "d": "internal_note",
            "f": "selector_note",
            "h": "vendor_notes",
            "i": "vendor_title_no",
            "m": "blanket_po",
        },
    }
    BOOKOPS_MARC_BIB_MAPPING: dict[str, str | dict[str, str]] = {
        "barcodes": "barcodes",
        "branch_call_number": "branch_call_no",
        "control_number": "control_number",
        "isbn": "isbn",
        "research_call_number": "research_call_no",
        "title": "title",
        "upc": "upc_number",
        "update_date": {"tag": "005"},
    }
    BOOKOPS_MARC_ORDER_MAPPING: dict[str, str | dict[str, str]] = {
        "audience": "audn",
        "branches": "branches",
        "copies": "copies",
        "create_date": "created",
        "format": "form",
        "lang": "lang",
        "locations": "locs",
        "order_id": "order_id",
        "shelves": "shelves",
        "status": "status",
        "vendor_notes": "venNotes",
        "_field": {
            "c": "order_code_1",
            "d": "order_code_2",
            "e": "order_code_3",
            "f": "order_code_4",
            "i": "order_type",
            "s": "price",
            "u": "fund",
            "v": "vendor_code",
            "x": "country",
        },
        "_following_field": {
            "d": "internal_note",
            "f": "selector_note",
            "i": "vendor_title_no",
            "m": "blanket_po",
        },
    }

    def __init__(
        self,
        marc_mapping: dict[str, dict[str, str]] = MARC_ORDER_MAPPING,
    ) -> None:
        """
        Initialize `BookopsMarcParser` for a specific library.

        Args:
            library: library whose records are being parsed as a `LibrarySystem` obj
        """
        self.marc_mapping = marc_mapping

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
            for k, v in self.MARC_ORDER_MAPPING[tag].items():
                tag_dict[k] = getattr(order, v)
            out[tag] = tag_dict
        return out

    def _map_order_from_marc(self, order: BookopsMarcOrder) -> dict:
        """
        Factory method used to construct an `Order` object from a
        `bookops_marc.Order` object.

        Args:
            order: an order from a `bookops_marc.Bib` or `bookops_marc.Order` object

        Returns:
            an instance of the domain `Order` dataclass populated from MARC data.
        """
        out: dict[str, Any] = {}

        for k, v in self.BOOKOPS_MARC_ORDER_MAPPING.items():
            if isinstance(v, str):
                out[k] = getattr(order, v)
            else:
                field = getattr(order, k)
                for code, attr in v.items():
                    out[attr] = field.get(code) if field else None
        out["order_id"] = (
            models.bibs.OrderId(value=out["order_id"]) if out["order_id"] else None
        )
        return out

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

        out["bib_id"] = (
            models.bibs.BibId(bib.sierra_bib_id) if bib.sierra_bib_id else None
        )
        out["library"] = models.bibs.LibrarySystem(bib.library)
        out["collection"] = models.bibs.Collection(str(bib.collection).upper())
        out["orders"] = [
            models.bibs.Order(**self._map_order_from_marc(i)) for i in bib.orders
        ]
        out["oclc_number"] = list(bib.oclc_nos.values())
        for k, v in self.BOOKOPS_MARC_BIB_MAPPING.items():
            if isinstance(v, dict):
                out[k] = str(bib.get(v["tag"]))
            else:
                out[k] = getattr(bib, v)
        return models.bibs.DomainBib(**out)

    def _check_vendor_tag(
        self, record: dto.BibDTO, vendor_tags: dict[str, dict[str, str]]
    ) -> dict[str, str]:
        bib_dict: dict = {}
        for field, data in vendor_tags.items():
            bib_field = record.bib.get(field)
            if not bib_field:
                continue
            else:
                bib_dict[field] = {
                    "code": data["code"],
                    "value": bib_field.get(data["code"]),
                }
        return bib_dict

    def identify_vendor(
        self, record: dto.BibDTO, vendor_rules: dict[str, Any]
    ) -> dict[str, Any]:
        logger.info(f"Identifying vendor for record: {record.__dict__}")
        for vendor, info in vendor_rules.items():
            vendor_tags = info.get("vendor_tags", {})
            alt_vendor_tags = info.get("alternate_vendor_tags", {})
            tag_match = self._check_vendor_tag(record=record, vendor_tags=vendor_tags)
            if tag_match and tag_match == vendor_tags:
                return vendor_rules[vendor]
            alt_tag_match = self._check_vendor_tag(
                record=record, vendor_tags=alt_vendor_tags
            )
            if alt_tag_match and alt_tag_match == alt_vendor_tags:
                return vendor_rules[vendor]
        return vendor_rules["UNKNOWN"]

    def parse(
        self, data: BinaryIO | bytes, library: models.bibs.LibrarySystem
    ) -> list[dto.BibDTO]:
        """
        Parse binary MARC data into a list of `BibDTO` objects.

        Args:
            data: MARC records as file-like object or byte stream.

        Returns:
            a list of `BibDTO` objects containing `bookops_marc.Bib` objects
            and `DomainBib` objects.
        """
        records = []
        reader = SierraBibReader(data, library=str(library), hide_utf8_warnings=True)
        for record in reader:
            mapped_domain_bib = self._map_bib_from_marc(bib=record)
            logger.info(f"Vendor record parsed: {mapped_domain_bib}")
            obj = dto.BibDTO(bib=record, domain_bib=mapped_domain_bib)
            records.append(obj)
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

    def update_bib_fields(
        self, record: dto.BibDTO, fields: list[dict[str, str]]
    ) -> dto.BibDTO:
        """
        Update a `BibDTO` object's `Bib` attribute with new fields.

        Args:
            record: `BibDTO` object representing the bibliographic record.
            fields: a list of new MARC fields to insert as dictionaries.

        Returns:
            the updated record as a `BibDTO` object
        """
        bib_rec = copy.deepcopy(record.bib)
        if record.domain_bib.bib_id:
            bib_rec.remove_fields("907")
            bib_id_str = f".b{str(record.domain_bib.bib_id).strip('.b')}"
            bib_rec.add_ordered_field(
                Field(
                    tag="907",
                    indicators=Indicators(" ", " "),
                    subfields=[Subfield(code="a", value=bib_id_str)],
                )
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

    def update_order_fields(self, record: dto.BibDTO) -> dto.BibDTO:
        """
        Update a `BibDTO` object's `Bib` attribute with new fields based on order data.

        Args:
            record: `BibDTO` object representing the bibliographic record.

        Returns:
            the updated record as a `BibDTO` object
        """
        bib_rec = copy.deepcopy(record.bib)
        for order in record.domain_bib.orders:
            order_data = self._map_order_data(order)
            for tag in ["960", "961"]:
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
