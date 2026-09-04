"""Domain services and models for identifying record matches."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from overload_web.domain.pvf import models
from overload_web.domain.shared import sierra_responses

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClassifiedCandidates:
    """Holds candidate matches and associated data."""

    matched: list
    mixed: list[str]
    other: list[str]

    @property
    def duplicates(self) -> list[str]:
        """A list of bib IDs for all matched records."""
        duplicates: list[str] = []
        if len(self.matched) > 1:
            return [i.bib_id for i in self.matched]
        return duplicates


class MatchAnalysis:
    """Components extracted from match review process."""

    def __init__(
        self,
        action: models.CatalogAction,
        call_number: str | None,
        call_number_match: bool,
        classified: ClassifiedCandidates,
        resource_id: str | None,
        target_bib_id: str | None,
        vendor: str | None,
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
        self.vendor = vendor

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "call_number": self.call_number,
            "call_number_match": self.call_number_match,
            "duplicate_records": self.duplicate_records,
            "mixed": self.mixed,
            "other": self.other,
            "resource_id": self.resource_id,
            "target_bib_id": self.target_bib_id,
            "target_call_no": self.target_call_no,
            "target_title": self.target_title,
            "updated_by_vendor": self.updated_by_vendor,
            "vendor": self.vendor,
        }


class BaseMatchAnalyzer(ABC):
    """Review matches identified by the `BibMatcher` service."""

    @abstractmethod
    def analyze(
        self, record: models.DomainBib, candidates: ClassifiedCandidates
    ) -> MatchAnalysis: ...  # pragma: no branch

    def classify_matches(
        self, record: models.DomainBib, matches: list
    ) -> ClassifiedCandidates:
        """Classify the candidate matches associated with this response."""
        if record.library == "bpl":
            matches = [sierra_responses.BPLSolrResponse(i) for i in matches]
        if record.library == "nypl":
            matches = [sierra_responses.NYPLPlatformResponse(i) for i in matches]
        matched, mixed, other = [], [], []
        for c in sorted(matches, key=lambda i: int(i.bib_id.strip(".b")), reverse=True):
            if c.collection == "MIXED":
                mixed.append(c.bib_id)
            elif c.collection == record.collection:
                matched.append(c)
            else:
                other.append(c.bib_id)

        return ClassifiedCandidates(matched, mixed, other)

    def determine_catalog_action(
        self, record: models.DomainBib, candidate: sierra_responses.BaseSierraResponse
    ) -> tuple[models.CatalogAction, bool]:
        """
        Determine whether to insert, attach, or overlay/update a bib record in Sierra
        based on matches
        """
        if candidate.cat_source == "inhouse":
            return models.CatalogAction.ATTACH, False
        if candidate.update_datetime and (
            not record.update_datetime
            or candidate.update_datetime > record.update_datetime
        ):
            return models.CatalogAction.UPDATE, True
        return models.CatalogAction.ATTACH, False


class MatchAnalyzerFactory:
    """Create a BaseMatchAnalyzer based on library, record_type and collection."""

    @staticmethod
    def make(library: str, record_type: str, collection: str) -> BaseMatchAnalyzer:
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


class AcquisitionsMatchAnalyzer(BaseMatchAnalyzer):
    def analyze(
        self, record: models.DomainBib, candidates: ClassifiedCandidates
    ) -> MatchAnalysis:
        return MatchAnalysis(
            action=models.CatalogAction.INSERT,
            call_number=record.call_number,
            call_number_match=True,
            classified=candidates,
            resource_id=record.resource_id,
            target_bib_id=record.bib_id,
            target_call_no=record.branch_call_number,
            target_title=record.title,
            vendor=record.vendor,
        )


class BPLCatMatchAnalyzer(BaseMatchAnalyzer):
    def analyze(
        self, record: models.DomainBib, candidates: ClassifiedCandidates
    ) -> MatchAnalysis:
        if not candidates.matched:
            if record.vendor in ["Midwest DVD", "Midwest Audio", "Midwest CD"]:
                action = models.CatalogAction.ATTACH
            else:
                action = models.CatalogAction.INSERT
            return MatchAnalysis(
                action=action,
                call_number=record.call_number,
                call_number_match=True,
                classified=candidates,
                resource_id=record.resource_id,
                target_bib_id=record.bib_id,
                vendor=record.vendor,
            )
        for candidate in candidates.matched:
            if candidate.branch_call_number:
                if record.branch_call_number == candidate.branch_call_number:
                    action, updated = self.determine_catalog_action(
                        record=record, candidate=candidate
                    )
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
                        vendor=record.vendor,
                    )

        fallback = candidates.matched[-1]
        action, updated = self.determine_catalog_action(
            record=record, candidate=fallback
        )
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
            vendor=record.vendor,
        )


class NYPLCatResearchMatchAnalyzer(BaseMatchAnalyzer):
    def analyze(
        self, record: models.DomainBib, candidates: ClassifiedCandidates
    ) -> MatchAnalysis:
        if not candidates.matched:
            return MatchAnalysis(
                call_number_match=True,
                action=models.CatalogAction.INSERT,
                target_bib_id=None,
                call_number=record.call_number,
                resource_id=record.resource_id,
                classified=candidates,
                vendor=record.vendor,
            )
        for candidate in candidates.matched:
            if candidate.research_call_number:
                action, updated = self.determine_catalog_action(
                    record=record, candidate=candidate
                )
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
                    vendor=record.vendor,
                )
        last = candidates.matched[-1]
        return MatchAnalysis(
            call_number_match=False,
            action=models.CatalogAction.UPDATE,
            target_bib_id=last.bib_id,
            target_title=last.title,
            target_call_no=None,
            call_number=record.call_number,
            resource_id=record.resource_id,
            classified=candidates,
            vendor=record.vendor,
        )


class NYPLCatBranchMatchAnalyzer(BaseMatchAnalyzer):
    def analyze(
        self, record: models.DomainBib, candidates: ClassifiedCandidates
    ) -> MatchAnalysis:
        if not candidates.matched:
            return MatchAnalysis(
                call_number_match=True,
                action=models.CatalogAction.INSERT,
                target_bib_id=None,
                call_number=record.call_number,
                resource_id=record.resource_id,
                classified=candidates,
                vendor=record.vendor,
            )
        for candidate in candidates.matched:
            if (
                candidate.branch_call_number
                and record.branch_call_number == candidate.branch_call_number
            ):
                action, updated = self.determine_catalog_action(
                    record=record, candidate=candidate
                )
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
                    vendor=record.vendor,
                )

        fallback = candidates.matched[-1]
        action, updated = self.determine_catalog_action(
            record=record, candidate=fallback
        )
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
            vendor=record.vendor,
        )


class SelectionMatchAnalyzer(BaseMatchAnalyzer):
    def analyze(
        self, record: models.DomainBib, candidates: ClassifiedCandidates
    ) -> MatchAnalysis:
        if not candidates.matched:
            return MatchAnalysis(
                call_number_match=True,
                action=models.CatalogAction.INSERT,
                target_bib_id=None,
                call_number=record.call_number,
                resource_id=record.resource_id,
                classified=candidates,
                vendor=record.vendor,
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
                    action=models.CatalogAction.ATTACH,
                    target_bib_id=candidate.bib_id,
                    target_call_no=call_no,
                    target_title=candidate.title,
                    call_number=record.call_number,
                    resource_id=record.resource_id,
                    classified=candidates,
                    vendor=record.vendor,
                )
        fallback = candidates.matched[-1]
        return MatchAnalysis(
            call_number_match=True,
            action=models.CatalogAction.ATTACH,
            target_bib_id=fallback.bib_id,
            target_call_no=fallback.branch_call_number,
            target_title=fallback.title,
            call_number=record.call_number,
            resource_id=record.resource_id,
            classified=candidates,
            vendor=record.vendor,
        )
