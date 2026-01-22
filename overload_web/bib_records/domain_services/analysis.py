"""Domain service for reviewing matches for bib records.

This module includes implementations of the `MatchAnalyzer` protocol used to review
matches returned by the `BibMatcher` service. Each implementation contains logic
specific to the library to whom the record belongs and workflow being used.

Protocols:

`MatchAnalyzer`
    Protocol for reviewing matches identified by the `BibMatcher` service.



Child classes of `MatchAnalyzer`:

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

from overload_web.bib_records.domain_models import bibs, matches, sierra_responses

logger = logging.getLogger(__name__)


class MatchAnalyzer(Protocol):
    """Review matches identified by the `BibMatcher` service."""

    def _determine_catalog_action(
        self,
        bib: bibs.DomainBib,
        candidate: sierra_responses.BaseSierraResponse,
    ) -> tuple[matches.CatalogAction, bool]:
        if candidate.cat_source == "inhouse":
            return matches.CatalogAction.ATTACH, False
        if not bib.update_datetime or candidate.update_datetime > bib.update_datetime:
            return matches.CatalogAction.OVERLAY, True
        return matches.CatalogAction.ATTACH, False

    def analyze_match(
        self,
        record: bibs.DomainBib,
        candidates: list[sierra_responses.BaseSierraResponse],
    ) -> matches.MatchAnalysis: ...  # pragma: no branch


class AcquisitionsMatchAnalyzer(MatchAnalyzer):
    def analyze_match(
        self,
        record: bibs.DomainBib,
        candidates: list[sierra_responses.BaseSierraResponse],
    ) -> matches.MatchAnalysis:
        classified = record.classify_matches(candidates)
        match_ids = record.match_identifiers()
        vendor = record.vendor
        decision = matches.MatchDecision(
            action=matches.CatalogAction.INSERT, target_bib_id=record.bib_id
        )
        analysis = matches.MatchAnalysis(
            call_number_match=True,
            classified=classified,
            decision=decision,
            match_identifiers=match_ids,
            vendor=vendor,
            target_call_no=record.branch_call_number,
            target_title=record.title,
        )
        return analysis


class BPLCatMatchAnalyzer(MatchAnalyzer):
    def analyze_match(
        self,
        record: bibs.DomainBib,
        candidates: list[sierra_responses.BaseSierraResponse],
    ) -> matches.MatchAnalysis:
        classified = record.classify_matches(candidates)
        match_ids = record.match_identifiers()
        vendor = record.vendor
        if not classified.matched:
            if record.vendor in ["Midwest DVD", "Midwest Audio", "Midwest CD"]:
                decision = matches.MatchDecision(
                    action=matches.CatalogAction.ATTACH, target_bib_id=record.bib_id
                )
            else:
                decision = matches.MatchDecision(
                    action=matches.CatalogAction.INSERT, target_bib_id=record.bib_id
                )
            analysis = matches.MatchAnalysis(
                call_number_match=True,
                classified=classified,
                decision=decision,
                match_identifiers=match_ids,
                vendor=vendor,
                target_call_no=record.branch_call_number,
                target_title=record.title,
            )
            return analysis
        for candidate in classified.matched:
            if candidate.branch_call_number:
                if record.branch_call_number == candidate.branch_call_number:
                    action, updated = self._determine_catalog_action(record, candidate)
                    decision = matches.MatchDecision(
                        action=action,
                        target_bib_id=candidate.bib_id,
                        updated_by_vendor=updated,
                    )
                    analysis = matches.MatchAnalysis(
                        call_number_match=True,
                        classified=classified,
                        decision=decision,
                        match_identifiers=match_ids,
                        vendor=vendor,
                        target_call_no=candidate.branch_call_number,
                        target_title=candidate.title,
                    )
                    return analysis
        fallback = classified.matched[-1]
        action, updated = self._determine_catalog_action(record, fallback)
        decision = matches.MatchDecision(
            action=action,
            target_bib_id=fallback.bib_id,
            updated_by_vendor=updated,
        )
        analysis = matches.MatchAnalysis(
            call_number_match=False,
            classified=classified,
            decision=decision,
            match_identifiers=match_ids,
            vendor=vendor,
            target_call_no=fallback.branch_call_number,
            target_title=fallback.title,
        )
        return analysis


class NYPLCatResearchMatchAnalyzer(MatchAnalyzer):
    def analyze_match(
        self,
        record: bibs.DomainBib,
        candidates: list[sierra_responses.BaseSierraResponse],
    ) -> matches.MatchAnalysis:
        classified = record.classify_matches(candidates)
        match_ids = record.match_identifiers()
        vendor = record.vendor
        if not classified.matched:
            decision = matches.MatchDecision(
                action=matches.CatalogAction.INSERT, target_bib_id=None
            )
            analysis = matches.MatchAnalysis(
                call_number_match=True,
                classified=classified,
                decision=decision,
                match_identifiers=match_ids,
                vendor=vendor,
            )
            return analysis
        for candidate in classified.matched:
            if candidate.research_call_number:
                action, updated = self._determine_catalog_action(record, candidate)
                decision = matches.MatchDecision(
                    action=action,
                    target_bib_id=candidate.bib_id,
                    updated_by_vendor=updated,
                )
                analysis = matches.MatchAnalysis(
                    call_number_match=True,
                    classified=classified,
                    decision=decision,
                    match_identifiers=match_ids,
                    vendor=vendor,
                    target_title=candidate.title,
                    target_call_no=candidate.research_call_number[0],
                )
                return analysis
        last = classified.matched[-1]
        decision = matches.MatchDecision(
            action=matches.CatalogAction.OVERLAY, target_bib_id=last.bib_id
        )
        analysis = matches.MatchAnalysis(
            call_number_match=False,
            classified=classified,
            decision=decision,
            match_identifiers=match_ids,
            vendor=vendor,
            target_title=last.title,
            target_call_no=None,
        )
        return analysis


class NYPLCatBranchMatchAnalyzer(MatchAnalyzer):
    def analyze_match(
        self,
        record: bibs.DomainBib,
        candidates: list[sierra_responses.BaseSierraResponse],
    ) -> matches.MatchAnalysis:
        classified = record.classify_matches(candidates)
        match_ids = record.match_identifiers()
        vendor = record.vendor
        if not classified.matched:
            decision = matches.MatchDecision(
                action=matches.CatalogAction.INSERT, target_bib_id=None
            )
            analysis = matches.MatchAnalysis(
                call_number_match=True,
                classified=classified,
                decision=decision,
                match_identifiers=match_ids,
                vendor=vendor,
            )
            return analysis
        for candidate in classified.matched:
            if (
                candidate.branch_call_number
                and record.branch_call_number == candidate.branch_call_number
            ):
                action, updated = self._determine_catalog_action(record, candidate)
                decision = matches.MatchDecision(
                    action=action,
                    target_bib_id=candidate.bib_id,
                    updated_by_vendor=updated,
                )
                analysis = matches.MatchAnalysis(
                    call_number_match=True,
                    classified=classified,
                    decision=decision,
                    match_identifiers=match_ids,
                    vendor=vendor,
                    target_title=candidate.title,
                    target_call_no=candidate.branch_call_number,
                )
                return analysis

        fallback = classified.matched[-1]
        action, updated = self._determine_catalog_action(record, fallback)
        decision = matches.MatchDecision(
            action=action, target_bib_id=fallback.bib_id, updated_by_vendor=updated
        )
        analysis = matches.MatchAnalysis(
            call_number_match=False,
            classified=classified,
            decision=decision,
            match_identifiers=match_ids,
            vendor=vendor,
            target_title=fallback.title,
            target_call_no=fallback.branch_call_number,
        )
        return analysis


class SelectionMatchAnalyzer(MatchAnalyzer):
    def analyze_match(
        self,
        record: bibs.DomainBib,
        candidates: list[sierra_responses.BaseSierraResponse],
    ) -> matches.MatchAnalysis:
        classified = record.classify_matches(candidates)
        match_ids = record.match_identifiers()
        vendor = record.vendor
        if not classified.matched:
            decision = matches.MatchDecision(
                action=matches.CatalogAction.INSERT, target_bib_id=None
            )
            analysis = matches.MatchAnalysis(
                call_number_match=True,
                classified=classified,
                decision=decision,
                match_identifiers=match_ids,
                vendor=vendor,
            )
            return analysis
        for candidate in classified.matched:
            if candidate.branch_call_number or len(candidate.research_call_number) > 0:
                decision = matches.MatchDecision(
                    action=matches.CatalogAction.ATTACH, target_bib_id=candidate.bib_id
                )
                analysis = matches.MatchAnalysis(
                    call_number_match=True,
                    classified=classified,
                    decision=decision,
                    match_identifiers=match_ids,
                    vendor=vendor,
                    target_call_no=candidate.branch_call_number,
                    target_title=candidate.title,
                )
                return analysis
        fallback = classified.matched[-1]
        decision = matches.MatchDecision(
            action=matches.CatalogAction.ATTACH, target_bib_id=fallback.bib_id
        )
        analysis = matches.MatchAnalysis(
            call_number_match=True,
            classified=classified,
            decision=decision,
            match_identifiers=match_ids,
            vendor=vendor,
            target_call_no=fallback.branch_call_number,
            target_title=fallback.title,
        )
        return analysis
