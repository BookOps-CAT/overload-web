"""Adapter module defining classes used to parse and update MARC records.

Includes wrapper that allows for MARC records to be translated from pymarc/bookops_marc
objects to domain objects. The `MarcUpdater`also updates fields and the
`MarcParserEngine` also extracts values from fields.

Protocols:

`DomainBibProtocol`
    A protocol that defines a `DomainBib` used in this application. Defined in order
    to not have infrastructure layer dependent on domain layer.

Classes:

`MarcParserEngine`
    Parse binary MARC data using `bookops_marc` and `pymarc`. Uses config data
    to determine field mapping and processing workflows.
`MarcUpdater`
    Update binary MARC data using `bookops_marc` and `pymarc`. Uses config data
    to determine field mapping and processing workflows.
"""

from __future__ import annotations

import io
import logging
from typing import Any, BinaryIO, Protocol

from bookops_marc import Bib, SierraBibReader
from bookops_marc.models import Order
from pymarc import Field, Indicators, Subfield

logger = logging.getLogger(__name__)


class DomainBibProtocol(Protocol):
    library: str
    binary_data: bytes


class TargetProtocol(Protocol):
    tag: str
    indicators: tuple[str, str]
    code: str
    value: str


class MarcUpdater:
    """Interacts with binary MARC data using `bookops_marc`."""

    def _find_specific_field(self, bib: Bib, target: TargetProtocol) -> Field | None:
        """Find a field based on generic domain criteria."""
        for field in bib.get_fields(target.tag):
            subfield = field.get(target.code, "")
            if field.indicators == target.indicators and subfield == target.value:
                return field
        return None

    def create_bib_from_domain(self, record: DomainBibProtocol) -> Bib:
        """Create a `bookops_marc.Bib` object from a `DomainBib` object"""
        return Bib(data=record.binary_data, library=record.library)  # type: ignore

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
            if update.delete_all_by_tag is True:
                bib.remove_fields(update.delete_all_by_tag)
            if update.target_to_delete is not None:
                to_delete = self._find_specific_field(bib, update.target_to_delete)
                if to_delete:
                    bib.remove_field(to_delete)
            bib.add_ordered_field(
                Field(
                    tag=update.tag,
                    indicators=Indicators(update.ind1, update.ind2),
                    subfields=[
                        Subfield(code=i["code"], value=i["value"])
                        for i in update.subfields
                    ],
                )
            )

    def update_leader_encoding(self, leader: str, bib: Bib) -> None:
        """
        Update a bib record's leader[9] value to indicate unicode character encoding.

        Args:
            bib:
                A MARC record as a `bookops_marc.Bib` object
            leader:
                A MARC leader as a string

        Returns:
            None. The record's leader is updated in place.
        """
        bib.leader = leader[:9] + "a" + leader[10:]


class MarcParser:
    """Interacts with binary MARC data using `bookops_marc`."""

    def compare_mapped_tags(self, obj: Bib, tags: dict[str, dict[str, str]]) -> bool:
        """
        Get the MARC tag, subfield code, and subfield value from a record based on a
        dictionary containing tags and subfield codes.

        Args:
            obj: A `bookops_marc.Bib` object
            tags: A dictionary containing MARC tags, subfield codes, and subfield values

        Returns:
            A dictionary containing the values present in the MARC fields/subfields.

        """
        bib_dict: dict = {}
        for tag, data in tags.items():
            fields = obj.get_fields(tag)
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

    def create_bib_obj(self, data: bytes | BinaryIO, library: str) -> Bib:
        """Instantiate a `SierraBibReader` to read MARC binary data."""
        return Bib(data, library=library)  # type: ignore

    def get_reader(self, data: bytes | BinaryIO, library: str) -> SierraBibReader:
        """Instantiate a `SierraBibReader` to read MARC binary data."""
        return SierraBibReader(data, library=library)

    def identify_vendor(self, obj: Bib, mapping: dict[str, Any]) -> dict[str, Any]:
        """Determine the vendor who created a `bookops_marc.Bib` record."""
        for vendor, info in mapping[obj.library].items():
            tags = info["vendor_tags"].get("primary", {})
            tag_match = self.compare_mapped_tags(obj=obj, tags=tags)
            if tag_match:
                return info
            alt_tags = info["vendor_tags"].get("alternate", {})
            alt_match = self.compare_mapped_tags(obj=obj, tags=alt_tags)
            if alt_match:
                return info
        return mapping[obj.library]["UNKNOWN"]

    def map_bib_data(self, obj: Bib, mapping: dict[str, Any]) -> dict[str, Any]:
        """
        Build a dictionary representing a `DomainBib` object
        from a `bookops_marc.Bib` object and a set of mapping rules.

        Args:
            obj: MARC record represented as a `bookops_marc.Bib` object.

        Returns:
            a dictionary containing a mapping between a `bookops_marc` object
            and a domain object.
        """
        out: dict[str, Any] = {}
        # Adds or removes OCLC prefix from `001` field based on library
        obj.normalize_oclc_control_number()
        for k, v in mapping.items():
            # OCLC Numbers have to be converted from a list to a dictionary
            if v == "oclc_nos":
                property = getattr(obj, v)
                out[k] = list(set(property.values()))
            elif isinstance(v, dict) and "tag" in v:
                field = obj.get(v["tag"])
                out[k] = getattr(field, "data")
            # most attrs have 1:1 mapping between `Bib` and `DomainBib`
            else:
                out[k] = getattr(obj, v)
        parsed_fields: list[dict[str, Any]] = []
        for field in obj.get_fields():
            if field.is_control_field():
                parsed_fields.append({"tag": field.tag, "value": field.data})
            else:
                parsed_fields.append(
                    {
                        "tag": field.tag,
                        "indicators": (field.indicator1, field.indicator2),
                        "subfields": [
                            {"code": sf.code, "value": sf.value}
                            for sf in field.subfields
                        ],
                    }
                )
        out["parsed_fields"] = parsed_fields
        return out

    def map_order_data(self, obj: Order, mapping: dict[str, Any]) -> dict[str, Any]:
        """
        Build a dictionary representing a domain `Order` object
        from a `bookops_marc.Order` object and a set of mapping rules.

        Args:
            obj: a `bookops_marc.Order` object.

        Returns:
            a dictionary containing a mapping between a `bookops_marc` object
            and a domain object.
        """
        out: dict[str, Any] = {}

        for k, v in mapping.items():
            # most attrs have 1:1 mapping
            if isinstance(v, str):
                out[k] = getattr(obj, v)
            # nested dict for `bookops_marc.Order` attrs nested in fields
            else:
                field = getattr(obj, k)
                for code, attr in v.items():
                    out[attr] = field.get(code) if field else None
        return out

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
