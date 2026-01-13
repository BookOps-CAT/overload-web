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

    def review_candidates(
        self,
        candidates: list[sierra_responses.MatcherResponse],
    ) -> tuple[
        list[sierra_responses.MatchResolution], list[bibs.DomainBib]
    ]: ...  # pragma: no branch


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
        resolution = self.resolve(response)
        response.apply_matched_bib_id(bib_id=resolution.target_bib_id)
        return (resolution, response.bib)

    def resolve(
        self, response: sierra_responses.MatcherResponse
    ) -> sierra_responses.MatchResolution:
        raise NotImplementedError


class NYPLCatResearchMatchAnalyzer(BaseMatchAnalyzer):
    def resolve(
        self, response: sierra_responses.MatcherResponse
    ) -> sierra_responses.MatchResolution:
        classified = response.classify()

        if not classified.matched:
            return sierra_responses.MatchResolution(
                duplicate_records=classified.duplicates,
                target_bib_id=None,
                action=sierra_responses.CatalogAction.INSERT,
                call_number_match=True,
                input_call_no=response.input_call_no,
                resource_id=response.resource_id,
            )

        for candidate in classified.matched:
            if candidate.research_call_number:
                action, updated = self._determine_catalog_action(
                    response.bib, candidate
                )
                return sierra_responses.MatchResolution(
                    duplicate_records=classified.duplicates,
                    target_bib_id=candidate.bib_id,
                    action=action,
                    call_number_match=True,
                    updated_by_vendor=updated,
                    input_call_no=response.input_call_no,
                    resource_id=response.resource_id,
                )

        last = classified.matched[-1]
        return sierra_responses.MatchResolution(
            duplicate_records=classified.duplicates,
            target_bib_id=last.bib_id,
            action=sierra_responses.CatalogAction.OVERLAY,
            call_number_match=False,
            input_call_no=response.input_call_no,
            resource_id=response.resource_id,
        )


class NYPLCatBranchMatchAnalyzer(BaseMatchAnalyzer):
    def resolve(
        self, response: sierra_responses.MatcherResponse
    ) -> sierra_responses.MatchResolution:
        classified = response.classify()
        if not classified.matched:
            return sierra_responses.MatchResolution(
                duplicate_records=classified.duplicates,
                target_bib_id=None,
                action=sierra_responses.CatalogAction.INSERT,
                call_number_match=True,
                input_call_no=response.input_call_no,
                resource_id=response.resource_id,
            )

        for candidate in classified.matched:
            if (
                candidate.branch_call_number
                and response.bib.branch_call_number == candidate.branch_call_number
            ):
                action, updated = self._determine_catalog_action(
                    response.bib, candidate
                )
                return sierra_responses.MatchResolution(
                    duplicate_records=classified.duplicates,
                    target_bib_id=candidate.bib_id,
                    action=action,
                    call_number_match=True,
                    updated_by_vendor=updated,
                    input_call_no=response.input_call_no,
                    resource_id=response.resource_id,
                )

        fallback = classified.matched[-1]
        action, updated = self._determine_catalog_action(response.bib, fallback)

        return sierra_responses.MatchResolution(
            duplicate_records=classified.duplicates,
            target_bib_id=fallback.bib_id,
            action=action,
            call_number_match=False,
            updated_by_vendor=updated,
            input_call_no=response.input_call_no,
            resource_id=response.resource_id,
        )


class BPLCatMatchAnalyzer(BaseMatchAnalyzer):
    def resolve(
        self, response: sierra_responses.MatcherResponse
    ) -> sierra_responses.MatchResolution:
        classified = response.classify()
        if not classified.matched:
            if response.bib.vendor in ["Midwest DVD", "Midwest Audio", "Midwest CD"]:
                action = sierra_responses.CatalogAction.ATTACH
            else:
                action = sierra_responses.CatalogAction.INSERT
            return sierra_responses.MatchResolution(
                duplicate_records=classified.duplicates,
                target_bib_id=response.bib.bib_id,
                action=action,
                call_number_match=True,
                input_call_no=response.input_call_no,
                resource_id=response.resource_id,
            )
        for candidate in classified.matched:
            if candidate.branch_call_number:
                if response.bib.branch_call_number == candidate.branch_call_number:
                    action, updated = self._determine_catalog_action(
                        response.bib, candidate
                    )
                    return sierra_responses.MatchResolution(
                        duplicate_records=classified.duplicates,
                        target_bib_id=candidate.bib_id,
                        action=action,
                        call_number_match=True,
                        updated_by_vendor=updated,
                        input_call_no=response.input_call_no,
                        resource_id=response.resource_id,
                    )

        fallback = classified.matched[-1]
        action, updated = self._determine_catalog_action(response.bib, fallback)

        return sierra_responses.MatchResolution(
            duplicate_records=classified.duplicates,
            target_bib_id=fallback.bib_id,
            action=action,
            call_number_match=False,
            updated_by_vendor=updated,
            input_call_no=response.input_call_no,
            resource_id=response.resource_id,
        )


class SelectionMatchAnalyzer(BaseMatchAnalyzer):
    def resolve(
        self, response: sierra_responses.MatcherResponse
    ) -> sierra_responses.MatchResolution:
        classified = response.classify()
        if not classified.matched:
            return sierra_responses.MatchResolution(
                duplicate_records=classified.duplicates,
                target_bib_id=None,
                action=sierra_responses.CatalogAction.INSERT,
                call_number_match=True,
                input_call_no=response.input_call_no,
                resource_id=response.resource_id,
            )
        for candidate in classified.matched:
            if candidate.branch_call_number or len(candidate.research_call_number) > 0:
                return sierra_responses.MatchResolution(
                    duplicate_records=classified.duplicates,
                    target_bib_id=candidate.bib_id,
                    action=sierra_responses.CatalogAction.ATTACH,
                    call_number_match=True,
                    input_call_no=response.input_call_no,
                    resource_id=response.resource_id,
                )
        fallback = classified.matched[-1]
        return sierra_responses.MatchResolution(
            duplicate_records=classified.duplicates,
            target_bib_id=fallback.bib_id,
            action=sierra_responses.CatalogAction.ATTACH,
            call_number_match=True,
            input_call_no=response.input_call_no,
            resource_id=response.resource_id,
        )


class AcquisitionsMatchAnalyzer(BaseMatchAnalyzer):
    def resolve(
        self, response: sierra_responses.MatcherResponse
    ) -> sierra_responses.MatchResolution:
        classified = response.classify()
        return sierra_responses.MatchResolution(
            duplicate_records=classified.duplicates,
            target_bib_id=response.bib.bib_id,
            action=sierra_responses.CatalogAction.INSERT,
            call_number_match=True,
            input_call_no=response.input_call_no,
            resource_id=response.resource_id,
        )
