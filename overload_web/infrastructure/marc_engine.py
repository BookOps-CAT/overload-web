"""Adapter module defining classes used to parse and update MARC records.

Includes wrapper that allows for MARC records to be translated from pymarc/bookops_marc
objects to domain objects. The `MarcEngine` service also updates and extracts values
from fields.

Protocols:

`DomainBibProtocol`
    A protocol that defines a `DomainBib` used in this application. Defined in order
    to not have infrastructure layer dependent on domain layer.

Classes:

`MarcEngineConfig`
    Configuration data used to determine MARC record processing. Loaded from a .json
    file and input via an html form in the presentation layer.
`MarcEngine`
    Interact with binary MARC data using `bookops_marc` and `pymarc`. Uses config data
    to determine field mapping and processing workflows.
"""

from __future__ import annotations

import io
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
    bib_id_tag: str
    collection: str | None
    default_loc: str | None
    library: str
    marc_order_mapping: dict[str, Any]
    parser_bib_mapping: dict[str, Any]
    parser_order_mapping: dict[str, Any]
    parser_vendor_mapping: dict[str, Any]
    record_type: str


class MarcEngine:
    """Interacts with binary MARC data using `bookops_marc`."""

    def __init__(self, rules: MarcEngineConfig) -> None:
        """
        Initialize `MarcEngine` using a set of marc mapping rules and workflow inputs.

        This class is a concrete implementation of the `MarcEnginePort` protocol.

        Args:
            rules:
                A `MarcEngineConfig` object containing vendor identification
                rules, rules to use when mapping MARC records to domain objects, library
                and record type. Parsed from `/overload_web/data/mapping_specs.json` and
                values input by user for `library`, `collection`, and `record_type`.
        """
        self.library = rules.library
        self.collection = rules.collection
        self.record_type = rules.record_type
        self.config = rules

    def create_bib_from_domain(self, record: DomainBibProtocol) -> Bib:
        """Create a `bookops_marc.Bib` object from a `DomainBib` object"""
        return Bib(data=record.binary_data, library=record.library)  # type: ignore

    def get_command_tag_field(self, bib: Bib) -> Field | None:
        for field in bib.get_fields("949", []):
            if field.indicators == Indicators(" ", " ") and field.get(
                "a", ""
            ).startswith("*"):
                return field
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
                A list of updates to make to the record as `rules.MarcFieldUpdateValues`
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
            # OCLC Numbers have to be normalized from a dictionary
            if v == "oclc_nos":
                property = getattr(obj, v)
                out[k] = list(set(property.values()))
            # most attrs have 1:1 mapping between `Bib` and `DomainBib`
            elif isinstance(v, str):
                out[k] = getattr(obj, v)
            # dict containing control field tag whose value to assign to attr
            elif isinstance(v, dict) and "tag" in v:
                field = obj.get(v["tag"])
                if field is not None:
                    out[k] = str(field.data)
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

    def write(self, records: list[DomainBibProtocol]) -> bytes:
        """
        Serialize `DomainBib` objects into a binary MARC stream.

        Args:
            records:
                A list `DomainBib` objects.

        Returns:
            MARC binary as an an in-memory file stream.
        """
        io_data = io.BytesIO()
        for record in records:
            logger.info(f"Writing MARC binary for record: {record}")
            io_data.write(record.binary_data)
        io_data.seek(0)
        out = io_data.getvalue()
        return out
