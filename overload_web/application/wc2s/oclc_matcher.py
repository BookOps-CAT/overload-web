from __future__ import annotations

import logging

from overload_web.application import ports
from overload_web.domain.wc2s import worldcat

logger = logging.getLogger(__name__)


class WorldcatMatcher:
    ID_INDEX = {
        "lccn": "sn",
        "oclc_number": "no",
        "isbn": "sn",
        "issn": "sn",
        "upc": "sn",
    }
    MATERIAL_TYPE_MAPPING = {
        "print": "book-printbook",
        "large_print": "book-largeprint",
        "dvd": "video-dvd",
        "bluray": "video-bluray",
    }

    def __init__(self, fetcher: ports.OCLCBibFetcher) -> None:
        self.fetcher = fetcher

    def get_update_date(
        self, responses: list[worldcat.BriefRecordResult]
    ) -> list[worldcat.BriefRecordResult]:
        for response in responses:
            bib_json = self.fetcher.get_full_bib_json_by_id(value=response.oclc_number)
            date = bib_json.get("date", {})
            response.update_date = date.get("replaceDate", date.get("createDate"))
        return responses

    def get_record_matches(self, source: worldcat.SourceData) -> worldcat.MatchedResult:
        evaluator = worldcat.RecordEvaluator(source.record_level)
        payload = {
            "q": f"{self.ID_INDEX[source.id_type]}={source.id}",
            "inCatalogLanguage": "eng",
            "catalogSource": source.required_cataloging_agency,
            "itemSubType": self.MATERIAL_TYPE_MAPPING.get(source.material_type),
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

    def get_full_records(self, matches: list[worldcat.MatchedItem]) -> list[bytes]:
        full_records = []
        for item in matches:
            record = self.fetcher.get_full_bib_by_id(item.matched_oclc)
            full_records.append(record)
        return full_records
