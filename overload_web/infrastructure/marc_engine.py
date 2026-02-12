from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, BinaryIO, Protocol

from bookops_marc import Bib, SierraBibReader
from pymarc import Field, Indicators, Subfield

logger = logging.getLogger(__name__)


class DomainBibProtocol(Protocol):
    library: str
    binary_data: bytes


@dataclass(frozen=True)
class MarcEngineConfig:
    marc_order_mapping: dict[str, Any]
    default_loc: str | None
    bib_id_tag: str
    library: str
    record_type: str
    collection: str | None
    parser_bib_mapping: dict[str, Any]
    parser_order_mapping: dict[str, Any]
    parser_vendor_mapping: dict[str, Any]


class MarcEngine:
    """Interacts with binary MARC data using `bookops_marc`."""

    def __init__(self, rules: MarcEngineConfig) -> None:
        """
        Initialize `MarcEngine` using a set of marc mapping rules.

        This class is a concrete implementation of the `MarcEnginePort` protocol.

        Args:
            rules:
                A `MarcEngineConfig` object containing vendor identification
                rules, rules to use when mapping MARC records to domain objects, library
                and record type. Parsed from `/overload_web/data/mapping_specs.json`.
        """
        self.library = rules.library
        self.collection = rules.collection
        self.record_type = rules.record_type
        self.bib_rules = rules.parser_bib_mapping
        self.order_rules = rules.parser_order_mapping
        self.vendor_rules = rules.parser_vendor_mapping
        self.default_loc = rules.default_loc
        self.bib_id_tag = rules.bib_id_tag
        self.marc_order_mapping = rules.marc_order_mapping
        self._config = rules

    def create_bib_from_domain(self, record: DomainBibProtocol) -> Bib:
        """Create a `bookops_marc.Bib` object from a `DomainBib` object"""
        return Bib(record.binary_data, library=record.library)  # type: ignore

    def get_command_tag_field(self, bib: Bib) -> Field | None:
        for field in bib.get_fields("949", []):
            if field.indicators == Indicators(" ", " ") and field.get(
                "a", ""
            ).startswith("*"):
                return field
        return None

    def get_value_of_field(self, tag: str, bib: Bib) -> str | None:
        """Get the value of the first MARC field for a tag."""
        if tag in bib:
            return bib.get_fields(tag)[0].value()
        return None

    def get_reader(self, data: bytes | BinaryIO) -> SierraBibReader:
        """Instantiate a `SierraBibReader` to read MARC binary data."""
        return SierraBibReader(data, library=self.library)

    def get_vendor_tags_from_bib(
        self, record: Bib, tags: dict[str, dict[str, str]]
    ) -> bool:
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
        if bib_dict:
            return bib_dict == tags
        return False

    def update_fields(self, field_updates: list[Any], bib: Bib) -> None:
        """
        Update a bibliographic record.

        Args:
            bib:
                A MARC record as a `bookops_marc.Bib` object
            field_updates:
                A list of updates to make to the record as `rules.MarcFieldUpdate`
                objects

        Returns:
            None. The record's fields are updated in place.
        """
        for update in field_updates:
            if update.delete:
                bib.remove_fields(update.tag)
            if update.original:
                bib.remove_field(update.original)
            bib.add_ordered_field(
                Field(
                    tag=update.tag,
                    indicators=Indicators(update.ind1, update.ind1),
                    subfields=[
                        Subfield(code=i["code"], value=i["value"])
                        for i in update.subfields
                    ],
                )
            )

    def map_data(self, obj: Any, rules: dict[str, Any]) -> dict[str, Any]:
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

        for k, v in rules.items():
            # most attrs have 1:1 mapping between `Bib` and `DomainBib`
            if isinstance(v, str):
                out[k] = getattr(obj, v)
            # dict containing control field tag whose value to assign to attr
            elif isinstance(v, dict) and "tag" in v:
                field = obj.get(v["tag"])
                if field is not None:
                    out[k] = str(field.data)
            # dict containing additional info about nested data for attr
            elif isinstance(v, dict) and "name" in v:
                property = getattr(obj, v["name"])
                out[k] = list(property.values())
            # nested dict for `bookops_marc.Order` objects
            else:
                field = getattr(obj, k)
                for code, attr in v.items():
                    out[attr] = field.get(code) if field else None
        return out

    def identify_vendor(self, record: Bib, rules: dict[str, Any]) -> dict[str, Any]:
        """Determine the vendor who created a `bookops_marc.Bib` record."""
        for vendor, info in rules.items():
            tags = info["vendor_tags"].get("primary", {})
            tag_match = self.get_vendor_tags_from_bib(record=record, tags=tags)
            if tag_match:
                return info
            alt_tags = info["vendor_tags"].get("alternate", {})
            alt_match = self.get_vendor_tags_from_bib(record=record, tags=alt_tags)
            if alt_match:
                return info
        return rules["UNKNOWN"]
