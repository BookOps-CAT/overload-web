"""Domain services for the Worldcat2Sierra application."""

from __future__ import annotations

import logging
from enum import StrEnum

from overload_web.domain.wc2s import ports, worldcat

logger = logging.getLogger(__name__)


class IdIndex(StrEnum):
    """Metadata API index used by different unique identifier types."""

    LCCN = "sn"
    OCLC_NUMBER = "no"
    ISBN = "sn"
    ISSN = "sn"
    UPC = "sn"


class MaterialTypeMapping(StrEnum):
    """Metadata API material type for differnet formats."""

    PRINT = "book-printbook"
    LARGE_PRINT = "book-largeprint"
    DVD = "video-dvd"
    BLURAY = "video-bluray"


class WorldcatMatcher:
    """A domain service for identifying matching records in WorldCat."""

    def __init__(self, fetcher: ports.OCLCBibFetcher) -> None:
        """Initialize `WorldcatMatcher` instance.

        Args:
            fetcher: a `ports.OCLCBibFetcher` object.

        """
        self.fetcher = fetcher

    def get_update_date(
        self, responses: list[worldcat.BriefRecordResult]
    ) -> list[worldcat.BriefRecordResult]:
        """Get update date for an OCLC record from the full record in JSON."""
        for response in responses:
            bib_json = self.fetcher.get_full_bib_json_by_id(
                oclc_number=response.oclc_number
            )
            date = bib_json.get("date", {})
            response.update_datetime = date.get("replaceDate", date.get("createDate"))
        return responses

    def get_record_matches(
        self, source: worldcat.SourceData
    ) -> worldcat.MatchedResultBrief:
        """Search WorldCat for matches and parse and evaluate responses."""
        evaluator = worldcat.RecordEvaluator(source.record_level)
        payload = {
            "q": f"{IdIndex[source.id_type.upper()].value}={source.id}",
            "inCatalogLanguage": "eng",
            "catalogSource": source.required_cataloging_agency,
            "itemSubType": MaterialTypeMapping.__members__.get(
                source.material_type.upper(), None
            ),
            "limit": 50,
        }
        responses = self.fetcher.get_brief_bibs_by_id(
            params={k: v for k, v in payload.items() if v}
        )
        parsed = evaluator.parse_responses(responses=responses)
        if source.action == "upgrade" and parsed:
            parsed = self.get_update_date(parsed)
        filtered = evaluator.filter_brief_bib_matches(responses=parsed, source=source)
        return filtered

    def get_full_records(
        self, matches: list[worldcat.MatchedItem]
    ) -> list[worldcat.FullMatchedItem]:
        """Retrieve full records from WorldCat for matched brief bib records."""
        full_records = []
        for item in matches:
            record = self.fetcher.get_full_bib_by_id(item.matched_oclc)
            full_records.append(
                worldcat.FullMatchedItem(
                    id=item.id,
                    id_type=item.id_type,
                    status=item.status,
                    matched_oclc=item.matched_oclc,
                    full_record=record,
                )
            )
        return full_records
