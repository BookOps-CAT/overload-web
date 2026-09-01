"""Application serivce commands for the Worldcat2Sierra service."""

import logging
from typing import Any

from overload_web.application import ports
from overload_web.application.wc2s import oclc_matcher
from overload_web.domain.wc2s import worldcat

logger = logging.getLogger(__name__)


class MatchSierraRecords2Worldcat:
    @staticmethod
    def execute(
        fetcher: ports.OCLCBibFetcher, source_data: list[worldcat.SourceData]
    ) -> list[dict[str, Any]]:
        out = []
        matcher = oclc_matcher.WorldcatMatcher(fetcher)
        for record in source_data:
            matched = matcher.get_record_matches(source=record)
            out.append(matched)
        return [i.__dict__ for i in out]
