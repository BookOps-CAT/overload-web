"""Domain models that define bib records, order records, and their component parts."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Any

from overload_web.bib_records.domain import responses


@dataclass(frozen=True)
class BibId:
    """A dataclass to define a BibId as an entity"""

    value: str

    def __post_init__(self):
        """Validate that the Bib ID is a string"""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("BibId must be a non-empty string.")

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"BibId(value={self.value!r})"


class Collection(Enum):
    """Includes valid values for NYPL and BPL collection"""

    BRANCH = "BL"
    RESEARCH = "RL"
    MIXED = "MIXED"
    NONE = "NONE"

    def __str__(self):
        return self.value


class DomainBib:
    """
    A domain model representing a bib record and its associated order data.

    Attributes:
        library: the library to whom the record belongs as an enum or str.
        barcodes: list of barcodes associated with the record.
        bib_id: sierra bib ID.
        branch_call_number: branch call number for the record, if present.
        collection: the collection to whom the record belongs as an enum or str.
        control_number: the record's control number, if present.
        isbn: ISBN for the title, if present.
        oclc_number: OCLC number(s) identifying the record, if present.
        orders: list of orders associated with the record.
        research_call_number: research call number for the record, if present.
        title: the title associated with the record.
        upc: UPC number, if present.
        update_date: the date the record was last updated.
        vendor: the vendor to whom the record belongs, if applicable.
    """

    def __init__(
        self,
        library: LibrarySystem | str,
        barcodes: list[str] = [],
        bib_id: BibId | str | None = None,
        branch_call_number: str | list[str] | None = None,
        collection: Collection | str | None = None,
        control_number: str | None = None,
        isbn: str | None = None,
        oclc_number: str | list[str] | None = None,
        orders: list[Order] = [],
        research_call_number: str | list[str] | None = None,
        title: str | None = None,
        upc: str | None = None,
        update_date: datetime.datetime | str | None = None,
        vendor: str | None = None,
    ) -> None:
        self.barcodes = barcodes
        self.bib_id = BibId(bib_id) if isinstance(bib_id, str) else bib_id
        self.branch_call_number = branch_call_number
        self.collection = (
            Collection(str(collection).upper())
            if not isinstance(collection, Collection)
            else collection
        )
        self.control_number = control_number
        self.isbn = isbn
        self.library = LibrarySystem(library) if isinstance(library, str) else library
        self.oclc_number = oclc_number
        self.orders = orders
        self.research_call_number = research_call_number
        self.title = title
        self.upc = upc
        self.update_date = update_date
        self.vendor = vendor

    def apply_order_template(self, template_data: dict[str, Any]) -> None:
        """
        Apply template data to all orders in this bib record.

        Args:
            template_data: dictionary of order fields and values to overwrite

        Returns:
            None
        """
        for order in self.orders:
            order.apply_template(template_data=template_data)


class LibrarySystem(Enum):
    """Includes valid values for library system"""

    BPL = "bpl"
    NYPL = "nypl"

    def __str__(self):
        return self.value


class Order:
    """A domain model representing a Sierra order."""

    def __init__(
        self,
        audience: list[str],
        blanket_po: str | None,
        branches: list[str],
        copies: str | int | None,
        country: str | None,
        create_date: datetime.datetime | datetime.date | str | None,
        format: str | None,
        fund: str | None,
        internal_note: str | None,
        lang: str | None,
        locations: list[str],
        order_code_1: str | None,
        order_code_2: str | None,
        order_code_3: str | None,
        order_code_4: str | None,
        order_id: OrderId | str | None,
        order_type: str | None,
        price: str | int | None,
        selector_note: str | None,
        shelves: list[str],
        status: str | None,
        vendor_code: str | None,
        vendor_notes: str | None,
        vendor_title_no: str | None,
    ) -> None:
        self.audience = audience
        self.blanket_po = blanket_po
        self.branches = branches
        self.copies = copies
        self.country = country
        self.create_date = create_date
        self.format = format
        self.fund = fund
        self.internal_note = internal_note
        self.lang = lang
        self.locations = locations
        self.order_code_1 = order_code_1
        self.order_code_2 = order_code_2
        self.order_code_3 = order_code_3
        self.order_code_4 = order_code_4
        self.order_id = OrderId(order_id) if isinstance(order_id, str) else order_id
        self.order_type = order_type
        self.price = price
        self.selector_note = selector_note
        self.shelves = shelves
        self.status = status
        self.vendor_code = vendor_code
        self.vendor_notes = vendor_notes
        self.vendor_title_no = vendor_title_no

    def apply_template(self, template_data: dict[str, Any]) -> None:
        """
        Apply template data to the order, updating any matching, non-empty fields.

        Args:
            template_data: Field-value pairs to apply.
        """
        for k, v in template_data.items():
            if v and k in self.__dict__.keys():
                setattr(self, k, v)

    def map_to_marc(
        self, rules: dict[str, dict[str, str]]
    ) -> dict[str, dict[str, str | int | OrderId | list[str] | None]]:
        """
        Map order data to MARC using a set of mapping rules

        Args:
            rules: a dict defining the fields and subfields to map `Order` attributes to

        Returns:
            the attributes of the `Order` as a dict mapped to MARC fields and subfields
        """

        out = {}
        for key in rules.keys():
            tag_dict = {}
            for k, v in rules[key].items():
                tag_dict[k] = getattr(self, v)
            out[key] = tag_dict
        return out


@dataclass(frozen=True)
class OrderId:
    """A dataclass to define a OrderId as an entity"""

    value: str

    def __post_init__(self):
        """Validate that the order ID is a string"""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("OrderId must be a non-empty string.")

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"OrderId(value={self.value!r})"


class RecordType(Enum):
    """Includes valid values for record type"""

    FULL = "full"
    ORDER_LEVEL = "order_level"

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class VendorInfo:
    """A dataclass to define a vendor rules as an entity"""

    bib_fields: list[dict[str, str]]
    matchpoints: dict[str, str]
    name: str


class ReviewedResults:
    """
    Compare a `DomainBib` to a list of candidate bibs and select the best match.

    Args:
        input: the bib record to match as a `DomainBib`.
        results: a list of candidate bib records as dicts
        record_type: the type of record as an enum (either `FULL` or `ORDER_LEVEL`)

    Returns:
        The results as a `bibs.ReviewedResults` object.
    """

    def __init__(
        self,
        input: DomainBib,
        results: list[responses.FetcherResponseDict],
        record_type: RecordType,
    ) -> None:
        self.input = input
        self.results = results
        self.vendor = input.vendor
        self.record_type = record_type
        self.action = None

        self.matched_results: list[responses.FetcherResponseDict] = []
        self.mixed_results: list[responses.FetcherResponseDict] = []
        self.other_results: list[responses.FetcherResponseDict] = []

        self._sort_results()

    def _sort_results(self) -> None:
        sorted_results = sorted(
            self.results, key=lambda i: int(i["bib_id"].strip(".b"))
        )
        for result in sorted_results:
            if result["collection"] == "MIXED":
                self.mixed_results.append(result)
            elif result["collection"] == str(self.input.collection):
                self.matched_results.append(result)
            else:
                self.other_results.append(result)

    @property
    def duplicate_records(self) -> list[str]:
        duplicate_records: list[str] = []
        if len(self.matched_results) > 1:
            return [i["bib_id"] for i in self.matched_results]
        return duplicate_records

    @property
    def input_call_no(self) -> str | None:
        if str(self.input.collection) == "RL":
            call_no = self.input.research_call_number
            return call_no[0] if isinstance(call_no, list) else call_no
        elif str(self.input.collection) == "BL":
            call_no = self.input.branch_call_number
            return call_no[0] if isinstance(call_no, list) else call_no
        elif str(self.input.library) == "BPL":
            call_no = self.input.branch_call_number
            return call_no[0] if isinstance(call_no, list) else call_no
        return None

    @property
    def resource_id(self) -> str | None:
        if self.input.bib_id:
            return str(self.input.bib_id)
        elif self.input.control_number:
            return self.input.control_number
        elif self.input.isbn:
            return self.input.isbn
        elif self.input.oclc_number:
            return (
                self.input.oclc_number
                if isinstance(self.input.oclc_number, str)
                else self.input.oclc_number[0]
            )
        elif self.input.upc:
            return self.input.upc
        return None

    @property
    def target_bib_id(self) -> BibId | None:
        bib_id = None
        if len(self.matched_results) == 1:
            return BibId(self.matched_results[0]["bib_id"])
        elif len(self.matched_results) == 0:
            return bib_id
        for result in self.matched_results:
            if result.get("branch_call_number") or result.get("research_call_number"):
                return BibId(result["bib_id"])
        return bib_id
