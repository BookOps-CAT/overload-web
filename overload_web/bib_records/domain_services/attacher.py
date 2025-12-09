from __future__ import annotations

import logging

from overload_web.bib_records.domain import bibs, marc_protocols

logger = logging.getLogger(__name__)


class BibAttacher:
    def __init__(self, reviewer: marc_protocols.ResultsReviewer) -> None:
        self.reviewer = reviewer

    def attach(self, responses: list[bibs.MatcherResponse]) -> list[bibs.DomainBib]:
        out = []
        for response in responses:
            bib_id = self.reviewer.review_results(
                input=response.bib, results=response.matches
            )
            response.bib.bib_id = bib_id
            out.append(response.bib)
        return out
