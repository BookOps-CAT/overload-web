"""Domain models that define objects associated with match analysis"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum

from overload_web.bib_records.domain_models import bibs

logger = logging.getLogger(__name__)


class CatalogAction(StrEnum):
    """Valid values for a cataloging action."""

    ATTACH = "attach"
    OVERLAY = "overlay"
    INSERT = "insert"


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
        classified: bibs.ClassifiedCandidates,
        decision: MatchDecision,
        match_identifiers: bibs.DomainBibMatchIds,
        vendor: str | None,
        target_call_no: str | None = None,
        target_title: str | None = None,
    ) -> None:
        self.action = decision.action
        self.call_number = match_identifiers.call_number
        self.call_number_match = call_number_match
        self.decision = decision
        self.duplicate_records = classified.duplicates
        self.mixed = classified.mixed
        self.other = classified.other
        self.resource_id = match_identifiers.resource_id
        self.target_bib_id = decision.target_bib_id
        self.target_call_no = target_call_no
        self.target_title = target_title
        self.updated_by_vendor = decision.updated_by_vendor
        self.vendor = vendor
