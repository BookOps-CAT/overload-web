"""Parsers for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import copy
import io
import logging
from typing import Any, BinaryIO

from bookops_marc import Bib, SierraBibReader
from pymarc import Field, Indicators, Subfield

from overload_web.bib_records.domain import bibs

logger = logging.getLogger(__name__)


class BibDTO:
    """
    Data Transfer Object for MARC records.

    This class is responsible binding a MARC record and its associated
    domain bib.

    Attributes:
        bib: The original MARC record as a `bookops_marc.Bib` object.
        domain_bib: The `DomainBib` object associated with the MARC record.
        vendor_info: The `VendorInfo` object associated with the MARC record.

    """

    def __init__(
        self, bib: Bib, domain_bib: bibs.DomainBib, vendor_info: bibs.VendorInfo
    ):
        self.bib = bib
        self.domain_bib = domain_bib
        self.vendor_info = vendor_info


class BookopsMarcParser:
    """Parses and serializes MARC records based on domain objects."""

    def __init__(self, library: str, rules: dict[str, Any]) -> None:
        """
        Initialize `BookopsMarcParser` using a specific set of marc mapping rules.

        This class is a concrete implementation of the `MarcParser` protocol.

        Args:
            library:
                The library whose records are to be processed.
            rules:
                A dictionary containing vendor identification rules, and rules to use
                when mapping MARC records, to domain objects.
        """
        self.library = library
        self.rules = rules

    def _get_tag_from_bib(
        self, record: Bib, tags: dict[str, dict[str, str]]
    ) -> dict[str, dict[str, str]]:
        """
        Get the MARC tag, subfield code, and value from a record based on a dictionary
        containing tags and subfield codes that would be present in a vendor's records

        Args:
            record: A bookops_marc.Bib object
            tags: A dictionary containing MARC tags, subfield codes, and subfield values

        Returns:
            A dictionary containing the values present in the MARC fields/subfields.

        """
        bib_dict: dict = {}
        for tag, data in tags.items():
            field = record.get(tag)
            if not field:
                continue
            else:
                bib_dict[tag] = {"code": data["code"], "value": field.get(data["code"])}
        return bib_dict

    def _map_domain_bib_from_marc(self, record: Bib) -> bibs.DomainBib:
        """
        Factory method used to build a `DomainBib` from a `bookops_marc.Bib` object.

        Args:
            record: MARC record represented as a `bookops_marc.Bib` object.

        Returns:
            DomainBib: domain object populated with structured order and identifier
            data.
        """
        out: dict[str, Any] = {}

        marc_mapping = self.rules["bookops_marc_mapping"]
        out["oclc_number"] = list(record.oclc_nos.values())
        for k, v in marc_mapping["bib"].items():
            if isinstance(v, dict):
                out[k] = str(record.get(v["tag"]))
            else:
                out[k] = getattr(record, v)
        out["orders"] = []
        for order in record.orders:
            order_dict = {}
            for k, v in marc_mapping["order"].items():
                if isinstance(v, str):
                    order_dict[k] = getattr(order, v)
                else:
                    field = getattr(order, k)
                    for code, attr in v.items():
                        order_dict[attr] = field.get(code) if field else None
            out["orders"].append(bibs.Order(**order_dict))
        return bibs.DomainBib(**out)

    def identify_vendor(self, record: Bib) -> bibs.VendorInfo:
        """Identify the vendor to whom a `bookops_marc.Bib` record belongs."""
        vendor_tags = self.rules["vendor_tags"][self.library.casefold()]
        vendor_info = self.rules["vendor_info"][self.library.casefold()]
        for vendor, info in vendor_tags.items():
            fields = vendor_info.get(vendor, {}).get("bib_fields", [])
            matchpoints = vendor_info.get(vendor, {}).get("matchpoints", {})
            tags: dict[str, dict[str, str]] = info.get("primary", {})
            tag_match = self._get_tag_from_bib(record=record, tags=tags)
            if tag_match and tag_match == tags:
                return bibs.VendorInfo(
                    name=vendor, bib_fields=fields, matchpoints=matchpoints
                )
            alt_tags = info.get("alternate", {})
            alt_match = self._get_tag_from_bib(record=record, tags=alt_tags)
            if alt_match and alt_match == alt_tags:
                return bibs.VendorInfo(
                    name=vendor, bib_fields=fields, matchpoints=matchpoints
                )
        return bibs.VendorInfo(
            name="UNKNOWN",
            bib_fields=vendor_info["UNKNOWN"]["bib_fields"],
            matchpoints=vendor_info["UNKNOWN"]["matchpoints"],
        )

    def parse(self, data: BinaryIO | bytes) -> list[BibDTO]:
        """
        Parse binary MARC data into a list of `BibDTO` objects.

        Args:
            data: MARC records as file-like object or byte stream.

        Returns:
            a list of `BibDTO` objects containing `bookops_marc.Bib` objects
            and `DomainBib` objects.
        """
        records = []
        reader = SierraBibReader(data, library=self.library, hide_utf8_warnings=True)
        for record in reader:
            vendor_info = self.identify_vendor(record=record)
            mapped_domain_bib = self._map_domain_bib_from_marc(record=record)
            logger.info(f"Vendor record parsed: {mapped_domain_bib}")
            records.append(
                BibDTO(
                    bib=record, domain_bib=mapped_domain_bib, vendor_info=vendor_info
                )
            )
        return records

    def serialize(self, records: list[BibDTO]) -> BinaryIO:
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


class BookopsMarcUpdater:
    """Update MARC records based on attributes of domain objects."""

    def __init__(self, rules: dict[str, dict[str, str]]) -> None:
        """
        Initialize a `BookopsMarcUpdater` using a specific set of marc mapping rules.

        This class is a concrete implementation of the `MarcUpdater` protocol.

        Args:
            rules:
                A dictionary containing set of rules to use when mapping `Order`
                objects to MARC records. These rules map attributes of an `Order` to
                MARC fields and subfields.
        """
        self.rules = rules

    def update_bib_data(self, record: BibDTO) -> BibDTO:
        """Update the bib_id and add MARC fields to a `BibDTO` object."""
        bib_rec = copy.deepcopy(record.bib)
        if record.domain_bib.bib_id:
            bib_rec.remove_fields("907")
            bib_id = f".b{str(record.domain_bib.bib_id).strip('.b')}"
            bib_rec.add_ordered_field(
                Field(
                    tag="907",
                    indicators=Indicators(" ", " "),
                    subfields=[Subfield(code="a", value=bib_id)],
                )
            )
        for field in record.vendor_info.bib_fields:
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

    def update_order(self, record: BibDTO) -> BibDTO:
        """Update the MARC order fields within a `BibDTO` object."""
        bib_rec = copy.deepcopy(record.bib)
        for order in record.domain_bib.orders:
            order_data = order.map_to_marc(rules=self.rules)
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

    def update_record(
        self,
        record: BibDTO,
        record_type: bibs.RecordType,
        template_data: dict[str, Any] = {},
    ) -> BibDTO:
        """Update a MARC record based on its type and template data."""
        if record_type == bibs.RecordType.ORDER_LEVEL:
            record.domain_bib.apply_order_template(template_data=template_data)
            record = self.update_order(record=record)
        record = self.update_bib_data(record=record)
        return record
