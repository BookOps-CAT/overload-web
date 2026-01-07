"""Domain service for reviewing matches for bib records"""

from __future__ import annotations

import logging

from overload_web.bib_records.domain import bibs, marc_protocols

logger = logging.getLogger(__name__)


class BibReviewer:
    def __init__(self, strategy: marc_protocols.BibReviewStrategy) -> None:
        self.strategy = strategy

    def review_and_attach(
        self, responses: list[bibs.MatcherResponse]
    ) -> list[bibs.DomainBib]:
        out = []
        for response in responses:
            bib_id = self.strategy.review_results(
                input=response.bib, results=response.matches
            )
            response.bib.bib_id = bib_id
            out.append(response.bib)
        return out
