"""Parsers for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import logging
from typing import Any, BinaryIO

from bookops_marc import Bib, SierraBibReader
from pymarc import Field, Indicators, Subfield

from overload_web.bib_records.domain import bibs

logger = logging.getLogger(__name__)


class BookopsMarcMapper:
    """Parses MARC records based on domain objects."""

    def __init__(self, library: str, rules: dict[str, Any]) -> None:
        """
        Initialize `BookopsMarcParser` using a set of marc mapping rules.

        This class is a concrete implementation of the `MarcParser` protocol.

        Args:
            library:
                the library system to whom the records belong.
            rules:
                A dictionary containing vendor identification rules, and rules to use
                when mapping MARC records, to domain objects. Parsed from `mapper_rules`
                in `/overload_web/vendor_specs.json`.
        """
        self.library = library
        self.rules = rules

    def _get_marc_tag_from_bib(
        self, record: Bib, tags: dict[str, dict[str, str]]
    ) -> dict[str, dict[str, str]]:
        """
        Get the MARC tag, subfield code, and value from a record based on a dictionary
        containing tags and subfield codes that would be present in a vendor's records

        Args:
            record: A `bookops_marc.Bib` object
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

    def _identify_vendor(self, record: Bib) -> bibs.VendorInfo:
        """Determine the vendor who provided a `bookops_marc.Bib` record."""
        vendor_rules = self.rules["vendors"][record.library.casefold()]
        for vendor, info in vendor_rules.items():
            fields = info.get("bib_fields", [])
            matchpoints = info.get("matchpoints", {})
            tags = info["vendor_tags"].get("primary", {})
            tag_match = self._get_marc_tag_from_bib(record=record, tags=tags)
            if tag_match and tag_match == tags:
                return bibs.VendorInfo(
                    name=vendor, bib_fields=fields, matchpoints=matchpoints
                )
            alt_tags = info["vendor_tags"].get("alternate", {})
            alt_match = self._get_marc_tag_from_bib(record=record, tags=alt_tags)
            if alt_match and alt_match == alt_tags:
                return bibs.VendorInfo(
                    name=vendor, bib_fields=fields, matchpoints=matchpoints
                )
        return bibs.VendorInfo(
            name="UNKNOWN",
            bib_fields=vendor_rules["UNKNOWN"]["bib_fields"],
            matchpoints=vendor_rules["UNKNOWN"]["matchpoints"],
        )

    def _map_data(self, record: Bib) -> dict[str, Any]:
        """
        Factory method used to build a `DomainBib` from a `bookops_marc.Bib` object.

        Args:
            record: MARC record represented as a `bookops_marc.Bib` object.

        Returns:
            a dictionary containing a mapping between a `bookops_marc.Bib` object
            and a `DomainBib` object.
        """
        out: dict[str, Any] = {}

        out["oclc_number"] = list(record.oclc_nos.values())
        for k, v in self.rules["bib"].items():
            if isinstance(v, dict):
                out[k] = str(record.get(v["tag"]))
            else:
                out[k] = getattr(record, v)
        out["orders"] = []
        for order in record.orders:
            order_dict = {}
            for k, v in self.rules["order"].items():
                if isinstance(v, str):
                    order_dict[k] = getattr(order, v)
                else:
                    field = getattr(order, k)
                    for code, attr in v.items():
                        order_dict[attr] = field.get(code) if field else None
            out["orders"].append(bibs.Order(**order_dict))
        out["binary_data"] = record.as_marc()
        return out

    def map_order_bib(self, record: Bib) -> bibs.DomainBib:
        """
        Factory method used to build a `DomainBib` from a `bookops_marc.Bib` object
        for an order-level record.

        Args:
            record: MARC record represented as a `bookops_marc.Bib` object.

        Returns:
            a `bibs.DomainBib` object
        """
        out: dict[str, Any] = self._map_data(record=record)
        return bibs.DomainBib(**out)

    def map_full_bib(self, record: Bib) -> bibs.DomainBib:
        """
        Factory method used to build a `DomainBib` from a `bookops_marc.Bib` object
        for a full MARC record.

        Args:
            record: MARC record represented as a `bookops_marc.Bib` object.

        Returns:
            a `bibs.DomainBib` object
        """
        out: dict[str, Any] = {}
        out["vendor_info"] = self._identify_vendor(record=record)
        out.update(self._map_data(record=record))
        return bibs.DomainBib(**out)

    def map_full_bibs(self, data: BinaryIO | bytes) -> list[bibs.DomainBib]:
        """
        Factory method used to build `DomainBib` objects for full MARC records
        from binary data via `bookops_marc.Bib` objects.

        Args:
            data: MARC data represented in binary format

        Returns:
            a list of `bibs.DomainBib` objects mapped using bookops_marc
        """
        reader = SierraBibReader(data, library=self.library)
        parsed_recs = []
        for record in reader:
            out = self.map_full_bib(record=record)
            logger.info(f"Vendor record parsed: {out}")
            parsed_recs.append(out)
        return parsed_recs

    def map_order_bibs(self, data: BinaryIO | bytes) -> list[bibs.DomainBib]:
        """
        Factory method used to build `DomainBib` objects for order-level
        MARC records from binary data via `bookops_marc.Bib` objects.

        Args:
            data: MARC data represented in binary format

        Returns:
            a list of `bibs.DomainBib` objects mapped using bookops_marc
        """
        reader = SierraBibReader(data, library=self.library)
        parsed_recs = []
        for record in reader:
            out: dict[str, Any] = {}
            out["vendor_info"] = self._identify_vendor(record=record)
            out.update(self._map_data(record=record))
            logger.info(f"Vendor record parsed: {out}")
            parsed_recs.append(bibs.DomainBib(**out))
        return parsed_recs


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

    def update_bib_data(self, record: bibs.DomainBib) -> bibs.DomainBib:
        """Update the bib_id and add MARC fields to a `bibs.DomainBib` object."""
        bib_rec = Bib(record.binary_data, library=str(record.library))  # type: ignore
        if record.bib_id:
            bib_rec.remove_fields("907")
            bib_id = f".b{str(record.bib_id).strip('.b')}"
            bib_rec.add_ordered_field(
                Field(
                    tag="907",
                    indicators=Indicators(" ", " "),
                    subfields=[Subfield(code="a", value=bib_id)],
                )
            )
        for field in getattr(record.vendor_info, "bib_fields", []):
            bib_rec.add_ordered_field(
                Field(
                    tag=field["tag"],
                    indicators=Indicators(field["ind1"], field["ind2"]),
                    subfields=[
                        Subfield(code=field["subfield_code"], value=field["value"])
                    ],
                )
            )
        record.binary_data = bib_rec.as_marc()
        return record

    def update_order(self, record: bibs.DomainBib) -> bibs.DomainBib:
        """Update the MARC order fields within a `bibs.DomainBib` object."""
        bib_rec = Bib(record.binary_data, library=str(record.library))  # type: ignore
        for order in record.orders:
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
        record.binary_data = bib_rec.as_marc()
        return record

    def update_acquisitions_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        """Update a MARC record based on its type and template data."""
        record.apply_order_template(template_data=template_data)
        record = self.update_order(record=record)
        record = self.update_bib_data(record=record)
        return record

    def update_cataloging_record(self, record: bibs.DomainBib) -> bibs.DomainBib:
        """Update a MARC record based on its type and template data."""
        return self.update_bib_data(record=record)

    def update_selection_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        """Update a MARC record based on its type and template data."""
        record.apply_order_template(template_data=template_data)
        record = self.update_order(record=record)
        record = self.update_bib_data(record=record)
        return record
