"""Domain service for reviewing matches for bib records"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from overload_web.bib_records.domain_models import (
    bibs,
    sierra_responses,
)

logger = logging.getLogger(__name__)


class BaseMatchAnalyzer:
    def _determine_catalog_action(
        self,
        incoming: bibs.DomainBib,
        candidate: sierra_responses.BaseSierraResponse,
    ) -> tuple[sierra_responses.CatalogAction, bool]:
        if candidate.cat_source == "inhouse":
            return sierra_responses.CatalogAction.ATTACH, False

        if (
            not incoming.update_datetime
            or candidate.update_datetime > incoming.update_datetime
        ):
            return sierra_responses.CatalogAction.OVERLAY, True

        return sierra_responses.CatalogAction.ATTACH, False

    def review_candidates(
        self,
        candidates: list[sierra_responses.MatcherResponse],
    ) -> tuple[list[sierra_responses.MatchResolution], list[bibs.DomainBib]]:
        analysis_out = []
        bibs_out = []
        for candidate in candidates:
            analysis, bib = self.review_response(candidate)
            analysis_out.append(analysis)
            bibs_out.append(bib)
        return analysis_out, bibs_out

    def review_response(
        self,
        response: sierra_responses.MatcherResponse,
    ) -> tuple[sierra_responses.MatchResolution, bibs.DomainBib]:
        resolution = self.resolve(response.bib, response.matches)
        response.apply_matched_bib_id(bib_id=resolution.target_bib_id)
        return (resolution, response.bib)

    def resolve(
        self,
        incoming: bibs.DomainBib,
        candidates: list[sierra_responses.BaseSierraResponse],
    ) -> sierra_responses.MatchResolution:
        raise NotImplementedError


def get_input_call_no(incoming: bibs.DomainBib) -> str | None:
    call_no = None
    if str(incoming.library) == "nypl" and str(incoming.collection) == "RL":
        call_no = incoming.research_call_number
    else:
        call_no = incoming.branch_call_number
    if isinstance(call_no, list):
        return call_no[0]
    return call_no


def get_resource_id(incoming: bibs.DomainBib) -> str | None:
    if incoming.bib_id:
        return str(incoming.bib_id)
    elif incoming.control_number:
        return incoming.control_number
    elif incoming.isbn:
        return incoming.isbn
    elif incoming.oclc_number:
        return (
            incoming.oclc_number
            if isinstance(incoming.oclc_number, str)
            else incoming.oclc_number[0]
        )
    elif incoming.upc:
        return incoming.upc
    return None


@dataclass(frozen=True)
class ClassifiedCandidates:
    matched: list[sierra_responses.BaseSierraResponse]
    mixed: list[sierra_responses.BaseSierraResponse]
    other: list[sierra_responses.BaseSierraResponse]
    input_call_no: str | None
    resource_id: str | None

    @property
    def duplicates(self) -> list[str]:
        duplicates: list[str] = []
        if len(self.matched) > 1:
            return [i.bib_id for i in self.matched]
        return duplicates


class CandidateClassifier:
    @staticmethod
    def classify(
        incoming: bibs.DomainBib,
        candidates: list[sierra_responses.BaseSierraResponse],
    ) -> ClassifiedCandidates:
        matched, mixed, other = [], [], []
        input_call_no = get_input_call_no(incoming=incoming)
        resource_id = get_resource_id(incoming=incoming)
        for c in sorted(candidates, key=lambda i: int(i.bib_id.strip(".b"))):
            if c.library == "bpl":
                matched.append(c)
            elif c.collection == "MIXED":
                mixed.append(c)
            elif str(c.collection) == str(incoming.collection):
                matched.append(c)
            else:
                other.append(c)

        return ClassifiedCandidates(matched, mixed, other, input_call_no, resource_id)


class NYPLCatResearchMatchAnalyzer(BaseMatchAnalyzer):
    def resolve(
        self,
        incoming: bibs.DomainBib,
        candidates: list[sierra_responses.BaseSierraResponse],
    ) -> sierra_responses.MatchResolution:
        classified = CandidateClassifier.classify(incoming, candidates)

        if not classified.matched:
            return sierra_responses.MatchResolution(
                duplicate_records=classified.duplicates,
                target_bib_id=None,
                action=sierra_responses.CatalogAction.INSERT,
                call_number_match=True,
                input_call_no=classified.input_call_no,
                resource_id=classified.resource_id,
            )

        for candidate in classified.matched:
            if candidate.research_call_number:
                action, updated = self._determine_catalog_action(incoming, candidate)
                return sierra_responses.MatchResolution(
                    duplicate_records=classified.duplicates,
                    target_bib_id=candidate.bib_id,
                    action=action,
                    call_number_match=True,
                    updated_by_vendor=updated,
                    input_call_no=classified.input_call_no,
                    resource_id=classified.resource_id,
                )

        last = classified.matched[-1]
        return sierra_responses.MatchResolution(
            duplicate_records=classified.duplicates,
            target_bib_id=last.bib_id,
            action=sierra_responses.CatalogAction.OVERLAY,
            call_number_match=False,
            input_call_no=classified.input_call_no,
            resource_id=classified.resource_id,
        )


class NYPLCatBranchMatchAnalyzer(BaseMatchAnalyzer):
    def resolve(
        self,
        incoming: bibs.DomainBib,
        candidates: list[sierra_responses.BaseSierraResponse],
    ) -> sierra_responses.MatchResolution:
        classified = CandidateClassifier.classify(incoming, candidates)
        if not classified.matched:
            return sierra_responses.MatchResolution(
                duplicate_records=classified.duplicates,
                target_bib_id=None,
                action=sierra_responses.CatalogAction.INSERT,
                call_number_match=True,
                input_call_no=classified.input_call_no,
                resource_id=classified.resource_id,
            )

        for candidate in classified.matched:
            if (
                candidate.branch_call_number
                and incoming.branch_call_number == candidate.branch_call_number
            ):
                action, updated = self._determine_catalog_action(incoming, candidate)
                return sierra_responses.MatchResolution(
                    duplicate_records=classified.duplicates,
                    target_bib_id=candidate.bib_id,
                    action=action,
                    call_number_match=True,
                    updated_by_vendor=updated,
                    input_call_no=classified.input_call_no,
                    resource_id=classified.resource_id,
                )

        fallback = classified.matched[-1]
        action, updated = self._determine_catalog_action(incoming, fallback)

        return sierra_responses.MatchResolution(
            duplicate_records=classified.duplicates,
            target_bib_id=fallback.bib_id,
            action=action,
            call_number_match=False,
            updated_by_vendor=updated,
            input_call_no=classified.input_call_no,
            resource_id=classified.resource_id,
        )


class BPLCatMatchAnalyzer(BaseMatchAnalyzer):
    def resolve(
        self,
        incoming: bibs.DomainBib,
        candidates: list[sierra_responses.BaseSierraResponse],
    ) -> sierra_responses.MatchResolution:
        classified = CandidateClassifier.classify(incoming, candidates)
        if not classified.matched:
            if incoming.vendor in ["Midwest DVD", "Midwest Audio", "Midwest CD"]:
                action = sierra_responses.CatalogAction.ATTACH
            else:
                action = sierra_responses.CatalogAction.INSERT
            return sierra_responses.MatchResolution(
                duplicate_records=classified.duplicates,
                target_bib_id=incoming.bib_id,
                action=action,
                call_number_match=True,
                input_call_no=classified.input_call_no,
                resource_id=classified.resource_id,
            )
        for candidate in classified.matched:
            if candidate.branch_call_number:
                if incoming.branch_call_number == candidate.branch_call_number:
                    action, updated = self._determine_catalog_action(
                        incoming, candidate
                    )
                    return sierra_responses.MatchResolution(
                        duplicate_records=classified.duplicates,
                        target_bib_id=candidate.bib_id,
                        action=action,
                        call_number_match=True,
                        updated_by_vendor=updated,
                        input_call_no=classified.input_call_no,
                        resource_id=classified.resource_id,
                    )

        fallback = classified.matched[-1]
        action, updated = self._determine_catalog_action(incoming, fallback)

        return sierra_responses.MatchResolution(
            duplicate_records=classified.duplicates,
            target_bib_id=fallback.bib_id,
            action=action,
            call_number_match=False,
            updated_by_vendor=updated,
            input_call_no=classified.input_call_no,
            resource_id=classified.resource_id,
        )


class SelectionMatchAnalyzer(BaseMatchAnalyzer):
    def resolve(
        self,
        incoming: bibs.DomainBib,
        candidates: list[sierra_responses.BaseSierraResponse],
    ) -> sierra_responses.MatchResolution:
        classified = CandidateClassifier.classify(incoming, candidates)
        if not classified.matched:
            return sierra_responses.MatchResolution(
                duplicate_records=classified.duplicates,
                target_bib_id=None,
                action=sierra_responses.CatalogAction.INSERT,
                call_number_match=True,
                input_call_no=classified.input_call_no,
                resource_id=classified.resource_id,
            )
        for candidate in classified.matched:
            if candidate.branch_call_number or len(candidate.research_call_number) > 0:
                return sierra_responses.MatchResolution(
                    duplicate_records=classified.duplicates,
                    target_bib_id=candidate.bib_id,
                    action=sierra_responses.CatalogAction.ATTACH,
                    call_number_match=True,
                    input_call_no=classified.input_call_no,
                    resource_id=classified.resource_id,
                )
        fallback = classified.matched[-1]
        return sierra_responses.MatchResolution(
            duplicate_records=classified.duplicates,
            target_bib_id=fallback.bib_id,
            action=sierra_responses.CatalogAction.ATTACH,
            call_number_match=True,
            input_call_no=classified.input_call_no,
            resource_id=classified.resource_id,
        )


class AcquisitionsMatchAnalyzer(BaseMatchAnalyzer):
    def resolve(
        self,
        incoming: bibs.DomainBib,
        candidates: list[sierra_responses.BaseSierraResponse],
    ) -> sierra_responses.MatchResolution:
        classified = CandidateClassifier.classify(incoming, candidates)
        return sierra_responses.MatchResolution(
            duplicate_records=classified.duplicates,
            target_bib_id=incoming.bib_id,
            action=sierra_responses.CatalogAction.INSERT,
            call_number_match=True,
            input_call_no=classified.input_call_no,
            resource_id=classified.resource_id,
        )
