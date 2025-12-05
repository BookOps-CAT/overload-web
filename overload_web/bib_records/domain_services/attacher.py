from __future__ import annotations

import logging
from typing import Literal, overload

from overload_web.bib_records.domain import bibs, marc_protocols
from overload_web.errors import OverloadError

logger = logging.getLogger(__name__)


class BibAttacher:
    def __init__(self, reviewer: marc_protocols.ResultsReviewer) -> None:
        self.reviewer = reviewer

    def review_results(
        self, response: bibs.MatcherResponse, record_type: bibs.RecordType
    ) -> str | None:
        match record_type:
            case bibs.RecordType.ACQUISITIONS:
                return self.reviewer.review_acq_results(
                    input=response.bib, results=response.matches
                )
            case bibs.RecordType.CATALOGING:
                return self.reviewer.review_cat_results(
                    input=response.bib, results=response.matches
                )
            case bibs.RecordType.SELECTION:
                return self.reviewer.review_sel_results(
                    input=response.bib, results=response.matches
                )
            case _:
                raise OverloadError("Unknown record type.")

    @overload
    def attach(
        self,
        responses: list[bibs.MatcherResponse],
        record_type: Literal[bibs.RecordType.ACQUISITIONS],
    ) -> list[bibs.DomainBib]: ...  # pragma: no branch

    @overload
    def attach(
        self,
        responses: list[bibs.MatcherResponse],
        record_type: Literal[bibs.RecordType.CATALOGING],
    ) -> list[bibs.DomainBib]: ...  # pragma: no branch

    @overload
    def attach(
        self,
        responses: list[bibs.MatcherResponse],
        record_type: Literal[bibs.RecordType.SELECTION],
    ) -> list[bibs.DomainBib]: ...  # pragma: no branch

    def attach(
        self,
        responses: list[bibs.MatcherResponse],
        record_type: bibs.RecordType,
    ) -> list[bibs.DomainBib]:
        out = []
        for response in responses:
            bib_id = self.review_results(response=response, record_type=record_type)
            response.bib.bib_id = bib_id
            out.append(response.bib)
        return out
