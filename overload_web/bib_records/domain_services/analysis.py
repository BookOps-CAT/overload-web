"""Domain service for reviewing matches for bib records.

This module includes implementations of the `MatchAnalyzer` protocol used to review
matches returned by the `BibMatcher` service. Each implementation contains logic
specific to the library to whom the record belongs and workflow being used.

Protocols:

`MatchAnalyzer`
    Protocol for reviewing matches identified by the `BibMatcher` service.

Classes:

`BaseMatchAnalyzer`
    Base class for match analyzers providing shared functionality. Concrete
    implementation of the `MatchAnalyzer` protocol.

Child classes of `BaseMatchAnalyzer`:

`NYPLCatResearchMatchAnalyzer`
    Match analyzer for NYPL cataloging records belonging to the Research Library.
`NYPLCatBranchMatchAnalyzer`
    Match analyzer for NYPL cataloging records belonging to the Branch Libraries.
`BPLCatMatchAnalyzer`
    Match analyzer for BPL cataloging records.
`SelectionMatchAnalyzer`
    Match analyzer for selection workflow records.
`AcquisitionsMatchAnalyzer`
    Match analyzer for acquisitions workflow records.

"""

from __future__ import annotations

import logging
from typing import Protocol

from overload_web.bib_records.domain_models import bibs, sierra_responses

logger = logging.getLogger(__name__)


class MatchAnalyzer(Protocol):
    """Review matches identified by the `BibMatcher` service."""

    def analyze_matches(
        self,
        candidates: list[sierra_responses.MatchContext],
    ) -> list[sierra_responses.MatchAnalysis]: ...  # pragma: no branch


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

    def analyze_matches(
        self, candidates: list[sierra_responses.MatchContext]
    ) -> list[sierra_responses.MatchAnalysis]:
        analysis_out = []
        for candidate in candidates:
            analysis = self.review_response(candidate)
            analysis_out.append(analysis)
        return analysis_out

    def review_response(
        self, response: sierra_responses.MatchContext
    ) -> sierra_responses.MatchAnalysis:
        return self.analyze(response)

    def analyze(
        self, response: sierra_responses.MatchContext
    ) -> sierra_responses.MatchAnalysis:
        raise NotImplementedError


class NYPLCatResearchMatchAnalyzer(BaseMatchAnalyzer):
    def analyze(
        self, response: sierra_responses.MatchContext
    ) -> sierra_responses.MatchAnalysis:
        classified = response.classify()

        if not classified.matched:
            return sierra_responses.MatchAnalysis(
                classified=classified,
                action=sierra_responses.CatalogAction.INSERT,
                call_number_match=True,
                target=None,
                response=response,
                target_call_no=None,
            )

        for candidate in classified.matched:
            if candidate.research_call_number:
                action, updated = self._determine_catalog_action(
                    response.bib, candidate
                )
                return sierra_responses.MatchAnalysis(
                    classified=classified,
                    action=action,
                    call_number_match=True,
                    updated_by_vendor=updated,
                    target=candidate,
                    target_call_no=candidate.research_call_number[0],
                    response=response,
                )

        last = classified.matched[-1]
        return sierra_responses.MatchAnalysis(
            classified=classified,
            action=sierra_responses.CatalogAction.OVERLAY,
            call_number_match=False,
            target=last,
            target_call_no=None,
            response=response,
        )


class NYPLCatBranchMatchAnalyzer(BaseMatchAnalyzer):
    def analyze(
        self, response: sierra_responses.MatchContext
    ) -> sierra_responses.MatchAnalysis:
        classified = response.classify()
        if not classified.matched:
            return sierra_responses.MatchAnalysis(
                classified=classified,
                action=sierra_responses.CatalogAction.INSERT,
                call_number_match=True,
                target=None,
                target_call_no=None,
                response=response,
            )
        for candidate in classified.matched:
            if (
                candidate.branch_call_number
                and response.bib.branch_call_number == candidate.branch_call_number
            ):
                action, updated = self._determine_catalog_action(
                    response.bib, candidate
                )
                return sierra_responses.MatchAnalysis(
                    classified=classified,
                    action=action,
                    call_number_match=True,
                    updated_by_vendor=updated,
                    target=candidate,
                    response=response,
                    target_call_no=candidate.branch_call_number,
                )

        fallback = classified.matched[-1]
        action, updated = self._determine_catalog_action(response.bib, fallback)

        return sierra_responses.MatchAnalysis(
            classified=classified,
            action=action,
            call_number_match=False,
            updated_by_vendor=updated,
            target=fallback,
            target_call_no=fallback.branch_call_number,
            response=response,
        )


class BPLCatMatchAnalyzer(BaseMatchAnalyzer):
    def analyze(
        self, response: sierra_responses.MatchContext
    ) -> sierra_responses.MatchAnalysis:
        classified = response.classify()
        if not classified.matched:
            if response.bib.vendor in ["Midwest DVD", "Midwest Audio", "Midwest CD"]:
                action = sierra_responses.CatalogAction.ATTACH
            else:
                action = sierra_responses.CatalogAction.INSERT
            return sierra_responses.MatchAnalysis(
                classified=classified,
                action=action,
                call_number_match=True,
                target=response.bib,
                target_call_no=response.bib.branch_call_number,
                response=response,
            )
        for candidate in classified.matched:
            if candidate.branch_call_number:
                if response.bib.branch_call_number == candidate.branch_call_number:
                    action, updated = self._determine_catalog_action(
                        response.bib, candidate
                    )
                    return sierra_responses.MatchAnalysis(
                        classified=classified,
                        action=action,
                        call_number_match=True,
                        updated_by_vendor=updated,
                        target=candidate,
                        target_call_no=candidate.branch_call_number,
                        response=response,
                    )
        fallback = classified.matched[-1]
        action, updated = self._determine_catalog_action(response.bib, fallback)

        return sierra_responses.MatchAnalysis(
            classified=classified,
            action=action,
            call_number_match=False,
            updated_by_vendor=updated,
            target=fallback,
            target_call_no=fallback.branch_call_number,
            response=response,
        )


class SelectionMatchAnalyzer(BaseMatchAnalyzer):
    def analyze(
        self, response: sierra_responses.MatchContext
    ) -> sierra_responses.MatchAnalysis:
        classified = response.classify()
        if not classified.matched:
            return sierra_responses.MatchAnalysis(
                classified=classified,
                action=sierra_responses.CatalogAction.INSERT,
                call_number_match=True,
                target=None,
                target_call_no=None,
                response=response,
            )
        for candidate in classified.matched:
            if candidate.branch_call_number or len(candidate.research_call_number) > 0:
                return sierra_responses.MatchAnalysis(
                    classified=classified,
                    action=sierra_responses.CatalogAction.ATTACH,
                    call_number_match=True,
                    target=candidate,
                    target_call_no=candidate.branch_call_number,
                    response=response,
                )
        fallback = classified.matched[-1]
        return sierra_responses.MatchAnalysis(
            classified=classified,
            action=sierra_responses.CatalogAction.ATTACH,
            call_number_match=True,
            target=fallback,
            target_call_no=fallback.branch_call_number,
            response=response,
        )


class AcquisitionsMatchAnalyzer(BaseMatchAnalyzer):
    def analyze(
        self, response: sierra_responses.MatchContext
    ) -> sierra_responses.MatchAnalysis:
        classified = response.classify()
        return sierra_responses.MatchAnalysis(
            classified=classified,
            action=sierra_responses.CatalogAction.INSERT,
            call_number_match=True,
            target=response.bib,
            target_call_no=response.bib.branch_call_number,
            response=response,
        )
