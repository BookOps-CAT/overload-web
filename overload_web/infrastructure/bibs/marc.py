"""Parser for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import copy
import datetime
import io
from typing import BinaryIO

from bookops_marc import Bib, SierraBibReader
from bookops_marc.models import Order
from pymarc import Field, Indicators, Subfield

from overload_web.application import dto
from overload_web.domain import models, protocols


class BookopsMarcParser(protocols.bibs.MarcParser[dto.bib.BibDTO]):
    """Parses and serializes MARC records."""

    def __init__(
        self,
        library: models.bibs.LibrarySystem,
        marc_mapping: dict[str, dict[str, str]],
    ) -> None:
        """
        Initialize `BookopsMarcParser` for a specific library.

        Args:
            library: library whose records are being parsed as a `LibrarySystem` obj
        """
        self.library = library
        self.marc_mapping = marc_mapping
        self.mapper = BookopsMarcMapper()

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
            for k, v in self.marc_mapping[tag].items():
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
            mapped_domain_bib = self.mapper.map_bib(bib=record)
            obj = dto.bib.BibDTO(bib=record, domain_bib=mapped_domain_bib)
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
        self, record: dto.bib.BibDTO, fields: list[dict[str, str]]
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


class BookopsMarcMapper:
    def map_order(self, order: Order) -> models.bibs.Order:
        """
        Factory method used to construct an `Order` object from a
        `bookops_marc.Order` object.

        Args:
            order: an order from a `bookops_marc.Bib` or `bookops_marc.Order` object

        Returns:
            an instance of the domain `Order` dataclass populated from MARC data.
        """

        def from_following_field(code: str):
            if order._following_field:
                return order._following_field.get(code, None)
            return None

        return models.bibs.Order(
            audience=order.audn,
            blanket_po=from_following_field("m"),
            branches=order.branches,
            copies=order.copies,
            country=order._field.get("x", None),
            create_date=order.created,
            format=order.form,
            fund=order._field.get("u", None),
            internal_note=from_following_field("d"),
            lang=order.lang,
            locations=order.locs,
            order_code_1=order._field.get("c", None),
            order_code_2=order._field.get("d", None),
            order_code_3=order._field.get("e", None),
            order_code_4=order._field.get("f", None),
            order_type=order._field.get("i", None),
            order_id=(
                models.bibs.OrderId(value=str(order.order_id))
                if order.order_id
                else None
            ),
            price=order._field.get("s", None),
            selector_note=from_following_field("f"),
            shelves=order.shelves,
            status=order.status,
            vendor_code=order._field.get("v", None),
            vendor_notes=order.venNotes,
            vendor_title_no=from_following_field("i"),
        )

    def map_bib(self, bib: Bib) -> models.bibs.DomainBib:
        """
        Factory method used to build a `DomainBib` from a `bookops_marc.Bib` object.

        Args:
            bib: MARC record represented as a `bookops_marc.Bib` object.

        Returns:
            DomainBib: domain object populated with structured order and identifier data.
        """
        return models.bibs.DomainBib(
            library=models.bibs.LibrarySystem(bib.library),
            orders=[self.map_order(order=i) for i in bib.orders],
            bib_id=(
                models.bibs.BibId(value=bib.sierra_bib_id)
                if bib.sierra_bib_id
                else None
            ),
            upc=bib.upc_number,
            isbn=bib.isbn,
            oclc_number=list(bib.oclc_nos.values()),
            barcodes=bib.barcodes,
            call_number=(
                bib.research_call_no if bib.collection == "RL" else bib.branch_call_no
            ),
        )
