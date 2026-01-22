"""Domain models that define bib records, order records, and their component parts."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Optional


class CatalogAction(StrEnum):
    """Valid values for a cataloging action."""

    ATTACH = "attach"
    OVERLAY = "overlay"
    INSERT = "insert"


@dataclass(frozen=True)
class ClassifiedCandidates:
    """Holds candidate matches and associated data."""

    matched: list
    mixed: list[str]
    other: list[str]

    @property
    def duplicates(self) -> list[str]:
        duplicates: list[str] = []
        if len(self.matched) > 1:
            return [i.bib_id for i in self.matched]
        return duplicates


class Collection(StrEnum):
    """Valid values for NYPL and BPL collections"""

    BRANCH = "BL"
    RESEARCH = "RL"
    MIXED = "MIXED"
    NONE = "NONE"


class DomainBib:
    """A domain model representing a bib record and its associated order data."""

    def __init__(
        self,
        binary_data: bytes,
        collection: Collection | str | None,
        library: LibrarySystem | str,
        title: str,
        record_type: RecordType | str,
        barcodes: list[str] = [],
        bib_id: str | None = None,
        branch_call_number: str | None = None,
        control_number: str | None = None,
        isbn: str | None = None,
        oclc_number: str | list[str] | None = None,
        orders: list[Order] = [],
        research_call_number: str | list[str] | None = None,
        upc: str | None = None,
        update_date: str | None = None,
        vendor: str | None = None,
        vendor_info: VendorInfo | None = None,
    ) -> None:
        """
        Initialize a `DomainBib` object.

        Args:
            binary_data:
                The marc record as a byte literal or `bytes` object
            barcodes:
                The list of barcodes associated with the bib record as strings.
            bib_id:
                The record's sierra bib ID as a string.
            branch_call_number:
                The branch call number for the record, if present.
            collection:
                The collection to whom the record belongs as an enum (`Collection`)
                or str.
            control_number:
                The record's control number as a string, if present.
            isbn:
                The ISBN for the title as a string, if present.
            library:
                The library to whom the record belongs as an enum (`LibrarySystem`)
                or str.
            oclc_number:
                OCLC number(s) identifying the record as a string or list of strings,
                if present.
            orders:
                The list of orders associated with the record as `Order` domain objects.
            record_type:
                The workflow two whom this record belongs as an enum (`RecordType`)
                or str.
            research_call_number:
                The research call number for the record as a string or list of strings,
                if present.
            title:
                The title associated with the record as a string.
            upc:
                The UPC number associated with the record, if present.
            update_date:
                The date the record was last updated as a string following MARC 005
                formatting (ie. `YYYYMMDDHHMMSS.f`).
            vendor:
                The vendor to whom the record belongs as a string, if applicable.
            vendor_info:
                Info about the vendor as a `VendorInfo` object, if applicable.
        """

        self.barcodes = barcodes
        self.bib_id = bib_id
        self.binary_data = binary_data
        self.branch_call_number = branch_call_number
        self.collection = Collection(str(collection).upper())
        self.control_number = control_number
        self.isbn = isbn
        self.library = LibrarySystem(library)
        self.oclc_number = oclc_number
        self.orders = orders
        self.research_call_number = research_call_number
        self.record_type = RecordType(record_type)
        self.title = title
        self.upc = upc
        self.update_date = update_date
        self.vendor_info = vendor_info
        self.vendor = vendor if not vendor_info else vendor_info.name

    @property
    def update_datetime(self) -> datetime.datetime | None:
        """Creates `datetime.datetime` object from `update_date` string."""
        if self.update_date:
            return datetime.datetime.strptime(self.update_date, "%Y%m%d%H%M%S.%f")
        return None

    def apply_match_decision(self, decision: Any) -> None:
        self.update_bib_id(decision.target_bib_id)

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

    def classify_matches(self, matches: list) -> ClassifiedCandidates:
        """Classify the candidate matches associated with this response."""
        matched, mixed, other = [], [], []
        for c in sorted(matches, key=lambda i: int(i.bib_id.strip(".b")), reverse=True):
            if c.collection == "MIXED":
                mixed.append(c.bib_id)
            elif c.collection == self.collection:
                matched.append(c)
            else:
                other.append(c.bib_id)

        return ClassifiedCandidates(matched, mixed, other)

    def update_bib_id(self, bib_id: str | None) -> None:
        """
        Update a `DomainBib` object's bib_id.

        Args:
            bib_id: The new sierra bib ID as a string.

        Returns:
            None
        """
        if bib_id:
            self.bib_id = bib_id

    def match_identifiers(self) -> DomainBibMatchIds:
        """Determine call number and resource ID for bib record."""
        call_number, resource_id = None, None
        if self.library == "nypl" and self.collection == "RL":
            call_number = self.research_call_number
        else:
            call_number = self.branch_call_number
        if isinstance(call_number, list):
            call_number = call_number[0]
        if self.control_number:
            resource_id = self.control_number
        elif self.isbn:
            resource_id = self.isbn
        elif self.oclc_number and isinstance(self.oclc_number, str):
            resource_id = self.oclc_number
        elif self.oclc_number and isinstance(self.oclc_number, list):
            resource_id = self.oclc_number[0]
        elif self.upc:
            resource_id = self.upc
        return DomainBibMatchIds(call_number=call_number, resource_id=resource_id)

    def __repr__(self) -> str:
        return f"DomainBib(bib_id: {self.bib_id}, branch_call_number: {self.branch_call_number}, collection: {self.collection}, control_number: {self.control_number}, isbn: {self.isbn}, library: {self.library}, oclc_number: {self.oclc_number}, research_call_number: {self.research_call_number}, record_type: {self.record_type}, title: {self.title}, upc: {self.upc}, update_date: {self.update_date}, vendor: {self.vendor})"  # noqa: E501


@dataclass(frozen=True)
class DomainBibMatchIds:
    call_number: str | None
    resource_id: str | None


class LibrarySystem(StrEnum):
    """Valid values for library system"""

    BPL = "bpl"
    NYPL = "nypl"


class MatchAnalysis:
    """Components extracted from match review process."""

    def __init__(
        self,
        call_number_match: bool,
        classified: ClassifiedCandidates,
        collection: Collection,
        decision: MatchDecision,
        library: LibrarySystem,
        match_identifiers: DomainBibMatchIds,
        record_type: RecordType,
        vendor: str | None,
        target_call_no: str | None = None,
        target_title: str | None = None,
    ) -> None:
        self.action = decision.action
        self.call_number = match_identifiers.call_number
        self.call_number_match = call_number_match
        self.collection = collection
        self.decision = decision
        self.duplicate_records = classified.duplicates
        self.library = library
        self.mixed = classified.mixed
        self.other = classified.other
        self.record_type = record_type
        self.resource_id = match_identifiers.resource_id
        self.target_bib_id = decision.target_bib_id
        self.target_call_no = target_call_no
        self.target_title = target_title
        self.updated_by_vendor = decision.updated_by_vendor
        self.vendor = vendor


@dataclass(frozen=True)
class MatchDecision:
    action: CatalogAction
    target_bib_id: str | None
    updated_by_vendor: bool = False


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
        order_id: str | None,
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
        self.order_id = order_id
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
        Apply template data to the order.

        Identifies fields based on the key of a key/value pair and overwrites
        it with the value from the key/value pair if the attribute is not empty.

        Args:
            template_data: Field-value pairs to apply.
        """
        for k, v in template_data.items():
            if v and k in self.__dict__.keys():
                setattr(self, k, v)

    def map_to_marc(
        self, rules: dict[str, Any]
    ) -> dict[str, dict[str, str | int | list[str] | None]]:
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


class RecordType(StrEnum):
    """Valid values for record type/processing workflow."""

    ACQUISITIONS = "acq"
    CATALOGING = "cat"
    SELECTION = "sel"


@dataclass(frozen=True)
class VendorInfo:
    """A dataclass to define a vendor rules as an entity"""

    bib_fields: list[dict[str, str]]
    matchpoints: dict[str, str]
    name: str


class MatchAnalysisReport:
    def __init__(
        self, analyses: list[MatchAnalysis], barcodes: Optional[list[str]] = None
    ) -> None:
        self._analyses = analyses
        self.barcodes = barcodes
        self.action = tuple([i.action for i in self._analyses])
        self.call_number = tuple([i.call_number for i in self._analyses])
        self.call_number_match = tuple([i.call_number_match for i in self._analyses])
        self.collection = tuple([i.collection for i in self._analyses])
        self.duplicate_records = tuple(
            [",".join(i.duplicate_records) for i in self._analyses]
        )
        self.library = tuple([i.library for i in self._analyses])
        self.mixed = tuple([",".join(i.mixed) for i in self._analyses])
        self.other = tuple([",".join(i.other) for i in self._analyses])
        self.record_type = tuple([i.record_type for i in self._analyses])
        self.resource_id = tuple([i.resource_id for i in self._analyses])
        self.target_bib_id = tuple([i.target_bib_id for i in self._analyses])
        self.target_call_no = tuple([i.target_call_no for i in self._analyses])
        self.target_title = tuple([i.target_title for i in self._analyses])
        self.updated_by_vendor = tuple([i.updated_by_vendor for i in self._analyses])
        self.vendor = tuple([i.vendor for i in self._analyses])
        self.date = datetime.date.today().strftime("%y-%m-%d")

    def to_dict(self) -> Any:
        record_count = len(self.action)
        return {
            "resource_id": list(self.resource_id),
            "vendor": list(self.vendor),
            "updated_by_vendor": list(self.updated_by_vendor),
            "call_number_match": list(self.call_number_match),
            "target_call_no": list(self.target_call_no),
            "call_number": list(self.call_number),
            "duplicate_records": list(self.duplicate_records),
            "target_bib_id": list(self.target_bib_id),
            "target_title": list(self.target_title),
            "mixed": list(self.mixed),
            "other": list(self.other),
            "action": list(self.action),
            "library": list(self.library),
            "collection": list(self.collection),
            "record_type": list(self.record_type),
            "corrected": ["no"] * record_count,
            "date": datetime.date.today().strftime("%y-%m-%d"),
        }
