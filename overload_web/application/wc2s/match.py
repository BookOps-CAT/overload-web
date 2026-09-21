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
        fetcher: ports.OCLCBibFetcher,
        parser: ports.MarcParserPort,
        source_data: list[dict[str, Any]],
    ) -> list[worldcat.MatchedResultFull]:
        batches = []
        matcher = oclc_matcher.WorldcatMatcher(fetcher)
        for record in source_data:
            source = worldcat.SourceData(**record)
            result = matcher.get_record_matches(source=source)
            if result.matched is True and result.successful_matches:
                full_results = matcher.get_full_records(result.successful_matches)
                for full_result in full_results:
                    bib = parser.create_bib_obj(
                        library=source.library, data=full_result.full_record
                    )
                    full_result.full_record = bib
                batches.append(
                    worldcat.MatchedResultFull(
                        matched=result.matched,
                        failed_matches=result.failed_matches,
                        successful_matches=result.successful_matches,
                        full_record_matches=full_results,
                        source_data=source,
                    )
                )
            else:
                batches.append(
                    worldcat.MatchedResultFull(
                        matched=result.matched,
                        failed_matches=result.failed_matches,
                        successful_matches=result.successful_matches,
                        full_record_matches=[],
                        source_data=source,
                    )
                )
        # reader = parser.get_reader()
        return batches
