"""Adapter module defining classes used to parse and update MARC records.

Includes wrapper that allows for MARC records to be translated from pymarc/bookops_marc
objects to domain objects. The `MarcUpdateEngine`also updates fields and the
`MarcParserEngine` also extracts values from fields.

Protocols:

`DomainBibProtocol`
    A protocol that defines a `DomainBib` used in this application. Defined in order
    to not have infrastructure layer dependent on domain layer.

Classes:

`MarcParserEngine`
    Parse binary MARC data using `bookops_marc` and `pymarc`. Uses config data
    to determine field mapping and processing workflows.
`MarcUpdateEngine`
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


class MarcUpdateEngine:
    """Interacts with binary MARC data using `bookops_marc`."""

    def create_bib_from_domain(self, record: DomainBibProtocol) -> Bib:
        """Create a `bookops_marc.Bib` object from a `DomainBib` object"""
        return Bib(data=record.binary_data, library=record.library)  # type: ignore

    def get_command_tag(self, record: DomainBibProtocol) -> str | None:
        bib = Bib(data=record.binary_data, library=record.library)  # type: ignore
        for field in bib.get_fields("949"):
            if field.indicators == Indicators(" ", " ") and field.get(
                "a", ""
            ).startswith("*"):
                return field.get("a", "")
        return None

    def get_command_tag_field(self, bib: Bib) -> Field | None:
        for field in bib.get_fields("949"):
            if field.indicators == Indicators(" ", " ") and field.get(
                "a", ""
            ).startswith("*"):
                return field
        return None

    def _find_specific_field(self, bib: Bib, criteria: Any) -> Field | None:
        """Helper to find a field based on generic domain criteria."""
        for field in bib.get_fields(criteria.tag):
            if field.indicator1 != criteria.ind1 or field.indicator2 != criteria.ind2:
                continue
            sf_val = field.get(criteria.subfield_code, "")
            if criteria.subfield_starts_with and not sf_val.startswith(
                criteria.subfield_starts_with
            ):
                continue
            return field
        return None

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
            if update.delete_all_by_tag:
                bib.remove_fields(update.delete_all_by_tag)
            if update.target_to_delete:
                to_delete = self._find_specific_field(bib, update.target_to_delete)
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


class MarcParsingEngine:
    """Interacts with binary MARC data using `bookops_marc`."""

    def __init__(
        self,
        library: str,
        collection: str | None,
        record_type: str,
        bib_mapping: dict[str, Any],
        order_mapping: dict[str, Any],
        vendor_mapping: dict[str, Any],
    ) -> None:
        """
        Initialize `MarcParsingEngine` using a set of mapping rules and workflow inputs.

        This class is a concrete implementation of the `MarcParsingEnginePort` protocol.

        Args:
            library:
                the library whose records are being parsed
            collection:
                the collection to which the records belong
            record_type:
                the workflow two whom this record belongs
            bib_mapping:
                rules for mapping bookops_marc.Bib objects to domain objects
            order_mapping:
                rules for mapping bookops_marc.Order objects to domain objects
            vendor_mapping:
                rules for identifying the vendor to whom a record belongs
        """

        self.library = library
        self.collection = collection
        self.record_type = record_type
        self.bib_mapping = bib_mapping
        self.order_mapping = order_mapping
        self.vendor_mapping = vendor_mapping

    def get_reader(self, data: bytes | BinaryIO) -> SierraBibReader:
        """Instantiate a `SierraBibReader` to read MARC binary data."""
        return SierraBibReader(data, library=self.library)

    def match_vendor_tags_from_bib(
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

    def map_bib_data(self, obj: Bib) -> dict[str, Any]:
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

        obj.normalize_oclc_control_number()
        for k, v in self.bib_mapping.items():
            # OCLC Numbers have to be normalized from a dictionary
            if v == "oclc_nos":
                property = getattr(obj, v)
                out[k] = list(set(property.values()))
            elif isinstance(v, dict) and "tag" in v:
                field = obj.get(v["tag"])
                if field is not None:
                    out[k] = str(field.data)
            # most attrs have 1:1 mapping between `Bib` and `DomainBib`
            else:
                out[k] = getattr(obj, v)
        return out

    def map_order_data(self, obj: Order) -> dict[str, Any]:
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

        for k, v in self.order_mapping.items():
            # most attrs have 1:1 mapping
            if isinstance(v, str):
                out[k] = getattr(obj, v)
            # nested dict for `bookops_marc.Order` attrs nested in fields
            else:
                field = getattr(obj, k)
                for code, attr in v.items():
                    out[attr] = field.get(code) if field else None
        return out

    def identify_vendor(self, record: Bib) -> dict[str, Any]:
        """Determine the vendor who created a `bookops_marc.Bib` record."""
        for vendor, info in self.vendor_mapping[record.library].items():
            tags = info["vendor_tags"].get("primary", {})
            tag_match = self.match_vendor_tags_from_bib(record=record, tags=tags)
            if tag_match:
                return info
            alt_tags = info["vendor_tags"].get("alternate", {})
            alt_match = self.match_vendor_tags_from_bib(record=record, tags=alt_tags)
            if alt_match:
                return info
        return self.vendor_mapping[record.library]["UNKNOWN"]

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
