"""Parsers for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import json
import logging
from typing import Any, BinaryIO

from bookops_marc import Bib, SierraBibReader

from overload_web.bib_records.domain import bibs, marc_protocols

logger = logging.getLogger(__name__)


class MapperFactory:
    def make(self, library: str, record_type: str) -> marc_protocols.BibMapper:
        with open("overload_web/vendor_specs.json", "r", encoding="utf-8") as fh:
            constants = json.load(fh)
        if record_type in ["acq", "sel"]:
            return BookopsMarcOrderBibMapper(
                library=library, rules=constants["mapper_rules"]
            )
        else:
            return BookopsMarcFullBibMapper(
                library=library, rules=constants["mapper_rules"]
            )


class BookopsMarcBaseMapper:
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
                field = record.get(v["tag"])
                if field is not None:
                    out[k] = str(field.data)
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


class BookopsMarcFullBibMapper(BookopsMarcBaseMapper):
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

    def map_bibs(self, data: BinaryIO | bytes) -> list[bibs.DomainBib]:
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
            bib_dict: dict[str, Any] = {}
            bib_dict["vendor_info"] = self._identify_vendor(record=record)
            bib_dict.update(self._map_data(record=record))
            out = bibs.DomainBib(**bib_dict)
            logger.info(f"Vendor record parsed: {out}")
            parsed_recs.append(out)
        return parsed_recs


class BookopsMarcOrderBibMapper(BookopsMarcBaseMapper):
    """Parses order-level MARC records based on domain objects."""

    def map_bibs(self, data: BinaryIO | bytes) -> list[bibs.DomainBib]:
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
            bib_dict: dict[str, Any] = self._map_data(record=record)
            out = bibs.DomainBib(**bib_dict)
            logger.info(f"Vendor record parsed: {out}")
            parsed_recs.append(out)
        return parsed_recs
