"""Application service commands for the Worldcat2Sierra service."""

import logging
from typing import Any

from overload_web.application import ports
from overload_web.application.wc2s import oclc_matcher
from overload_web.domain.wc2s import worldcat

logger = logging.getLogger(__name__)


class MatchWorldcat2Sierra:
    @staticmethod
    def execute(
        fetcher: ports.OCLCBibFetcher, source_data: list[worldcat.SourceData]
    ) -> list[Any]:
        batches = []
        matcher = oclc_matcher.WorldcatMatcher(fetcher)
        for record in source_data:
            result = matcher.get_record_matches(source=record)
            out = []
            if result.matched is True and result.successful_matches:
                full_results = matcher.get_full_records(result.successful_matches)
                out.append(full_results)
            batches.append(out)

        return batches
