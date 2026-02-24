"""Domain models that define bib records, order records, and their component parts."""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

from overload_web.domain.models import sierra_responses

logger = logging.getLogger(__name__)


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
    """A domain entity representing a bib record and its associated order data."""

    def __init__(
        self,
        binary_data: bytes,
        collection: Collection | str | None,
        library: LibrarySystem | str,
        record_type: RecordType | str,
        title: str,
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
        self._analysis: MatchAnalysis | None = None

    @property
    def analysis(self) -> MatchAnalysis:
        if self._analysis is None:
            raise AttributeError("MatchAnalysis has not been assigned to the DomainBib")
        return self._analysis

    @analysis.setter
    def analysis(self, value) -> None:
        self._analysis = value

    @property
    def call_number(self) -> str | None:
        """Determine call number for bib record."""
        if self.library == "nypl" and self.collection == "RL":
            call_number = self.research_call_number
        else:
            call_number = self.branch_call_number
        if isinstance(call_number, list):
            call_number = call_number[0] if call_number else None
        return call_number

    @property
    def resource_id(self) -> str | None:
        """Determine resource ID for bib record."""
        if self.control_number:
            return self.control_number
        elif self.isbn:
            return self.isbn
        elif self.oclc_number and isinstance(self.oclc_number, str):
            return self.oclc_number
        elif self.oclc_number and isinstance(self.oclc_number, list):
            return self.oclc_number[0]
        elif self.upc:
            return self.upc
        return None

    @property
    def update_datetime(self) -> datetime.datetime | None:
        """Creates `datetime.datetime` object from `update_date` string."""
        if self.update_date:
            return datetime.datetime.strptime(self.update_date, "%Y%m%d%H%M%S.%f")
        return None

    def apply_match(self, analysis: MatchAnalysis) -> None:
        """
        Update a `DomainBib` object's bib_id.

        Args:
            bib_id: The new sierra bib ID as a string.

        Returns:
            None
        """
        if analysis.target_bib_id and self.bib_id is None:
            self.bib_id = analysis.target_bib_id
        self._analysis = analysis

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
        if self.library == "bpl":
            matches = [sierra_responses.BPLSolrResponse(i) for i in matches]
        elif self.library == "nypl":
            matches = [sierra_responses.NYPLPlatformResponse(i) for i in matches]
        else:
            raise ValueError(
                f"Unknown library: {self.library}. Cannot classify matches."
            )
        matched, mixed, other = [], [], []
        for c in sorted(matches, key=lambda i: int(i.bib_id.strip(".b")), reverse=True):
            if c.collection == "MIXED":
                mixed.append(c.bib_id)
            elif c.collection == self.collection:
                matched.append(c)
            else:
                other.append(c.bib_id)

        return ClassifiedCandidates(matched, mixed, other)

    def determine_catalog_action(
        self, candidate: sierra_responses.BaseSierraResponse
    ) -> tuple[CatalogAction, bool]:
        if candidate.cat_source == "inhouse":
            return CatalogAction.ATTACH, False
        if not self.update_datetime or candidate.update_datetime > self.update_datetime:
            return CatalogAction.OVERLAY, True
        return CatalogAction.ATTACH, False

    def __repr__(self) -> str:
        return f"DomainBib(barcodes: {self.barcodes}, bib_id: {self.bib_id}, branch_call_number: {self.branch_call_number}, collection: {self.collection}, control_number: {self.control_number}, isbn: {self.isbn}, library: {self.library}, oclc_number: {self.oclc_number}, research_call_number: {self.research_call_number}, record_type: {self.record_type}, title: {self.title}, upc: {self.upc}, update_date: {self.update_date}, vendor: {self.vendor})"  # noqa: E501

    def analyze_matches(self, candidates: list[dict[str, Any]]) -> MatchAnalysis:
        classified = self.classify_matches(candidates)
        analyzer = MatchAnalyzerFactory().make(
            library=self.library,
            record_type=self.record_type,
            collection=self.collection,
        )
        logger.info(f"Analyzing matches with {analyzer.__class__.__name__}")
        return analyzer.analyze(record=self, candidates=classified)


class LibrarySystem(StrEnum):
    """Valid values for library system"""

    BPL = "bpl"
    NYPL = "nypl"


class MatchAnalysis:
    """Components extracted from match review process."""

    def __init__(
        self,
        call_number: str | None,
        call_number_match: bool,
        classified: ClassifiedCandidates,
        action: CatalogAction,
        resource_id: str | None,
        target_bib_id: str | None,
        target_call_no: str | None = None,
        target_title: str | None = None,
        updated_by_vendor: bool = False,
    ) -> None:
        self.action = action
        self.call_number = call_number
        self.call_number_match = call_number_match
        self.duplicate_records = classified.duplicates
        self.mixed = classified.mixed
        self.other = classified.other
        self.resource_id = resource_id
        self.target_bib_id = target_bib_id
        self.target_call_no = target_call_no
        self.target_title = target_title
        self.updated_by_vendor = updated_by_vendor


class MatchAnalyzer(Protocol):
    """Review matches identified by the `BibMatcher` service."""

    def analyze(
        self, record: DomainBib, candidates: ClassifiedCandidates
    ) -> MatchAnalysis: ...  # pragma: no branch


class MatchAnalyzerFactory:
    """Create a `MatchAnalyzer` based on `library`, `record_type` and `collection`"""

    def make(self, library: str, record_type: str, collection: str) -> MatchAnalyzer:
        match record_type, library, collection:
            case "cat", "nypl", "BL":
                return NYPLCatBranchMatchAnalyzer()
            case "cat", "nypl", "RL":
                return NYPLCatResearchMatchAnalyzer()
            case "cat", "bpl", _:
                return BPLCatMatchAnalyzer()
            case "sel", _, _:
                return SelectionMatchAnalyzer()
            case _:
                return AcquisitionsMatchAnalyzer()


@dataclass
class Order:
    """A domain model representing a Sierra order."""

    audience: list[str]
    blanket_po: str | None
    branches: list[str]
    copies: str | int | None
    country: str | None
    create_date: datetime.datetime | datetime.date | str | None
    format: str | None
    fund: str | None
    internal_note: str | None
    lang: str | None
    locations: list[str]
    order_code_1: str | None
    order_code_2: str | None
    order_code_3: str | None
    order_code_4: str | None
    order_id: str | None
    order_type: str | None
    price: str | int | None
    project_code: str | None
    selector_note: str | None
    shelves: list[str]
    status: str | None
    vendor_code: str | None
    vendor_notes: str | None
    vendor_title_no: str | None

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


@dataclass
class VendorInfo:
    """A dataclass to define a vendor rules as an entity"""

    bib_fields: list[dict[str, str]]
    matchpoints: dict[str, str]
    name: str
    vendor_tags: list[dict[str, str]] | None = None


class AcquisitionsMatchAnalyzer(MatchAnalyzer):
    def analyze(
        self, record: DomainBib, candidates: ClassifiedCandidates
    ) -> MatchAnalysis:
        return MatchAnalysis(
            action=CatalogAction.INSERT,
            call_number=record.call_number,
            call_number_match=True,
            classified=candidates,
            resource_id=record.resource_id,
            target_bib_id=record.bib_id,
            target_call_no=record.branch_call_number,
            target_title=record.title,
        )


class BPLCatMatchAnalyzer(MatchAnalyzer):
    def analyze(
        self, record: DomainBib, candidates: ClassifiedCandidates
    ) -> MatchAnalysis:
        if not candidates.matched:
            if record.vendor in ["Midwest DVD", "Midwest Audio", "Midwest CD"]:
                action = CatalogAction.ATTACH
            else:
                action = CatalogAction.INSERT
            return MatchAnalysis(
                action=action,
                call_number=record.call_number,
                call_number_match=True,
                classified=candidates,
                resource_id=record.resource_id,
                target_bib_id=record.bib_id,
                target_call_no=record.branch_call_number,
                target_title=record.title,
            )
        for candidate in candidates.matched:
            if candidate.branch_call_number:
                if record.branch_call_number == candidate.branch_call_number:
                    action, updated = record.determine_catalog_action(candidate)
                    return MatchAnalysis(
                        call_number_match=True,
                        call_number=record.call_number,
                        action=action,
                        resource_id=record.resource_id,
                        classified=candidates,
                        target_bib_id=candidate.bib_id,
                        target_call_no=candidate.branch_call_number,
                        target_title=candidate.title,
                        updated_by_vendor=updated,
                    )

        fallback = candidates.matched[-1]
        action, updated = record.determine_catalog_action(fallback)
        return MatchAnalysis(
            call_number_match=False,
            action=action,
            target_bib_id=fallback.bib_id,
            target_call_no=fallback.branch_call_number,
            target_title=fallback.title,
            updated_by_vendor=updated,
            call_number=record.call_number,
            resource_id=record.resource_id,
            classified=candidates,
        )


class NYPLCatResearchMatchAnalyzer(MatchAnalyzer):
    def analyze(
        self, record: DomainBib, candidates: ClassifiedCandidates
    ) -> MatchAnalysis:
        if not candidates.matched:
            return MatchAnalysis(
                call_number_match=True,
                action=CatalogAction.INSERT,
                target_bib_id=None,
                call_number=record.call_number,
                resource_id=record.resource_id,
                classified=candidates,
            )
        for candidate in candidates.matched:
            if candidate.research_call_number:
                action, updated = record.determine_catalog_action(candidate)
                return MatchAnalysis(
                    call_number_match=True,
                    action=action,
                    target_bib_id=candidate.bib_id,
                    target_title=candidate.title,
                    target_call_no=candidate.research_call_number[0],
                    updated_by_vendor=updated,
                    call_number=record.call_number,
                    resource_id=record.resource_id,
                    classified=candidates,
                )
        last = candidates.matched[-1]
        return MatchAnalysis(
            call_number_match=False,
            action=CatalogAction.OVERLAY,
            target_bib_id=last.bib_id,
            target_title=last.title,
            target_call_no=None,
            call_number=record.call_number,
            resource_id=record.resource_id,
            classified=candidates,
        )


class NYPLCatBranchMatchAnalyzer(MatchAnalyzer):
    def analyze(
        self, record: DomainBib, candidates: ClassifiedCandidates
    ) -> MatchAnalysis:
        if not candidates.matched:
            return MatchAnalysis(
                call_number_match=True,
                action=CatalogAction.INSERT,
                target_bib_id=None,
                call_number=record.call_number,
                resource_id=record.resource_id,
                classified=candidates,
            )
        for candidate in candidates.matched:
            if (
                candidate.branch_call_number
                and record.branch_call_number == candidate.branch_call_number
            ):
                action, updated = record.determine_catalog_action(candidate)
                return MatchAnalysis(
                    call_number_match=True,
                    action=action,
                    target_bib_id=candidate.bib_id,
                    target_title=candidate.title,
                    target_call_no=candidate.branch_call_number,
                    updated_by_vendor=updated,
                    call_number=record.call_number,
                    resource_id=record.resource_id,
                    classified=candidates,
                )

        fallback = candidates.matched[-1]
        action, updated = record.determine_catalog_action(fallback)
        return MatchAnalysis(
            call_number_match=False,
            action=action,
            target_bib_id=fallback.bib_id,
            updated_by_vendor=updated,
            target_title=fallback.title,
            target_call_no=fallback.branch_call_number,
            call_number=record.call_number,
            resource_id=record.resource_id,
            classified=candidates,
        )


class SelectionMatchAnalyzer(MatchAnalyzer):
    def analyze(
        self, record: DomainBib, candidates: ClassifiedCandidates
    ) -> MatchAnalysis:
        if not candidates.matched:
            return MatchAnalysis(
                call_number_match=True,
                action=CatalogAction.INSERT,
                target_bib_id=None,
                call_number=record.call_number,
                resource_id=record.resource_id,
                classified=candidates,
            )
        for candidate in candidates.matched:
            if candidate.branch_call_number:
                call_no = candidate.branch_call_number
            elif len(candidate.research_call_number) > 0:
                call_no = candidate.research_call_number[0]
            else:
                call_no = None
            if call_no:
                return MatchAnalysis(
                    call_number_match=True,
                    action=CatalogAction.ATTACH,
                    target_bib_id=candidate.bib_id,
                    target_call_no=call_no,
                    target_title=candidate.title,
                    call_number=record.call_number,
                    resource_id=record.resource_id,
                    classified=candidates,
                )
        fallback = candidates.matched[-1]
        return MatchAnalysis(
            call_number_match=True,
            action=CatalogAction.ATTACH,
            target_bib_id=fallback.bib_id,
            target_call_no=fallback.branch_call_number,
            target_title=fallback.title,
            call_number=record.call_number,
            resource_id=record.resource_id,
            classified=candidates,
        )
