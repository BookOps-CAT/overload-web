"""Domain models that define objects associated with match analysis"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum

from overload_web.bib_records.domain_models import bibs, sierra_responses

logger = logging.getLogger(__name__)


class CatalogAction(StrEnum):
    """Valid values for a cataloging action."""

    ATTACH = "attach"
    OVERLAY = "overlay"
    INSERT = "insert"


@dataclass(frozen=True)
class ClassifiedCandidates:
    """Holds candidate matches and associated data."""

    matched: list[sierra_responses.BaseSierraResponse]
    mixed: list[str]
    other: list[str]

    @property
    def duplicates(self) -> list[str]:
        duplicates: list[str] = []
        if len(self.matched) > 1:
            return [i.bib_id for i in self.matched]
        return duplicates


@dataclass(frozen=True)
class MatchContext:
    """A DTO that wraps a `DomainBib` object with its associated matches from Sierra."""

    bib: bibs.DomainBib
    candidates: list[sierra_responses.BaseSierraResponse]

    def classify(self) -> ClassifiedCandidates:
        """Classify the candidate matches associated with this response."""
        matched, mixed, other = [], [], []
        for c in sorted(
            self.candidates, key=lambda i: int(i.bib_id.strip(".b")), reverse=True
        ):
            if c.collection == "MIXED":
                mixed.append(c.bib_id)
            elif c.collection == self.bib.collection:
                matched.append(c)
            else:
                other.append(c.bib_id)

        return ClassifiedCandidates(matched, mixed, other)


@dataclass(frozen=True)
class MatchDecision:
    action: CatalogAction
    target_bib_id: str | None
    updated_by_vendor: bool = False


@dataclass(frozen=True)
class MatchDecisionResult:
    bib: bibs.DomainBib
    decision: MatchDecision
    analysis: MatchAnalysis


class MatchAnalysis:
    """Components extracted from match review process."""

    def __init__(
        self,
        call_number_match: bool,
        classified: ClassifiedCandidates,
        decision: MatchDecision,
        match_identifiers: bibs.DomainBibMatchIds,
        vendor: str | None,
        target_call_no: str | None = None,
        target_title: str | None = None,
    ) -> None:
        self.action = decision.action
        self.call_number = match_identifiers.call_number
        self.call_number_match = call_number_match
        self.duplicate_records = classified.duplicates
        self.mixed = classified.mixed
        self.other = classified.other
        self.resource_id = match_identifiers.resource_id
        self.target_bib_id = decision.target_bib_id
        self.target_call_no = target_call_no
        self.target_title = target_title
        self.updated_by_vendor = decision.updated_by_vendor
        self.vendor = vendor
