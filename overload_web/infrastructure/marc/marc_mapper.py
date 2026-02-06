"""Adapter module defining class used to parse MARC records into generics.

Includes `BookopsMarcMapper` class to parse records using `bookops_marc` and `pymarc`
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, BinaryIO

from bookops_marc import Bib, SierraBibReader

from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BibMapperConfig:
    parser_bib_mapping: dict[str, Any]
    parser_order_mapping: dict[str, Any]
    parser_vendor_mapping: dict[str, Any]
    library: str
    record_type: str


class MarcMapper:
    """Parses binary MARC data using `bookops_marc`."""

    def __init__(self, rules: BibMapperConfig) -> None:
        """
        Initialize `BookopsMarcMapper` using a set of marc mapping rules.

        This class is a concrete implementation of the `BibMapper` protocol.

        Args:
            rules:
                A `BibMapperConfig` object containing vendor identification
                rules, rules to use when mapping MARC records to domain objects, library
                and record type. Parsed from `/overload_web/data/mapping_specs.json`.
        """
        self.library = rules.library
        self.record_type = rules.record_type
        self.bib_rules = rules.parser_bib_mapping
        self.order_rules = rules.parser_order_mapping
        self.vendor_rules = rules.parser_vendor_mapping

    def _get_marc_tag_from_bib(
        self, record: Bib, tags: dict[str, dict[str, str]]
    ) -> dict[str, dict[str, str]]:
        """
        Get the MARC tag, subfield code, and subfield value from a record based on a
        dictionary containing tags and subfield codes.

        Args:
            record: A `bookops_marc.Bib` object
            tags: A dictionary containing MARC tags, subfield codes, and subfield values

        Returns:
            A dictionary containing the values present in the MARC fields/subfields.

        """
        bib_dict: dict = {}
        for tag, data in tags.items():
            fields = record.get_fields(tag)
            if not fields:
                continue
            values = [i.get(data["code"]) for i in fields]
            for value in values:
                if value != data["value"]:
                    continue
                bib_dict[tag] = {"code": data["code"], "value": value}
        return bib_dict

    def get_reader(self, data: bytes | BinaryIO) -> SierraBibReader:
        """Instantiate a `SierraBibReader` to read MARC binary data."""
        return SierraBibReader(data, library=self.library)

    def _map_data(self, record: Bib) -> dict[str, Any]:
        """
        Build a dictionary representing a `DomainBib` object from a
        `bookops_marc.Bib` object and a set of mapping rules.

        Args:
            record: MARC record represented as a `bookops_marc.Bib` object.

        Returns:
            a dictionary containing a mapping between a `bookops_marc.Bib` object
            and a `DomainBib` object.
        """
        out: dict[str, Any] = {}

        out["oclc_number"] = list(record.oclc_nos.values())
        for k, v in self.bib_rules.items():
            if isinstance(v, dict):
                field = record.get(v["tag"])
                if field is not None:
                    out[k] = str(field.data)
            else:
                out[k] = getattr(record, v)
        out["orders"] = []
        for order in record.orders:
            order_dict = {}
            for k, v in self.order_rules.items():
                if isinstance(v, str):
                    order_dict[k] = getattr(order, v)
                else:
                    field = getattr(order, k)
                    for code, attr in v.items():
                        order_dict[attr] = field.get(code) if field else None
            out["orders"].append(bibs.Order(**order_dict))
        out["binary_data"] = record.as_marc()
        out["record_type"] = self.record_type
        return out

    def identify_vendor(self, record: Bib) -> dict[str, Any]:
        """Determine the vendor who created a `bookops_marc.Bib` record."""
        for vendor, info in self.vendor_rules.items():
            fields = info.get("bib_fields", [])
            matchpoints = info.get("matchpoints", {})
            tags = info["vendor_tags"].get("primary", {})
            tag_match = self._get_marc_tag_from_bib(record=record, tags=tags)
            if tag_match and tag_match == tags:
                return {
                    "name": vendor,
                    "bib_fields": fields,
                    "matchpoints": matchpoints,
                }
            alt_tags = info["vendor_tags"].get("alternate", {})
            alt_match = self._get_marc_tag_from_bib(record=record, tags=alt_tags)
            if alt_match and alt_match == alt_tags:
                return {
                    "name": vendor,
                    "bib_fields": fields,
                    "matchpoints": matchpoints,
                }
        return {
            "name": "UNKNOWN",
            "bib_fields": self.vendor_rules["UNKNOWN"]["bib_fields"],
            "matchpoints": self.vendor_rules["UNKNOWN"]["matchpoints"],
        }

    def map_data(self, record: Bib, **kwargs) -> dict[str, Any]:
        """
        Build a dictionary representing a `DomainBib` object from a
        `bookops_marc.Bib` object and a set of mapping rules.

        Args:
            record:
                MARC record represented as a `bookops_marc.Bib` object.
            vendor:
                The vendor whose records are being parsed (for order-level
                records only)

        Returns:
            a dictionary containing a mapping between a `bookops_marc.Bib` object
            and a `DomainBib` object.
        """
        out = self._map_data(record=record)
        if out["record_type"] == "cat":
            out["vendor_info"] = bibs.VendorInfo(**self.identify_vendor(record=record))
        else:
            out["vendor"] = kwargs["vendor"]
        return out
