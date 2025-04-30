from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from overload_web.domain import model


@runtime_checkable
class BibFetcher(Protocol):
    def get_bibs_by_id(self, value: str | int, key: str) -> List[Dict[str, Any]]: ...


class BibMatchService:
    def __init__(self, fetcher: BibFetcher, matchpoints: Optional[List[str]] = None):
        self.fetcher = fetcher
        self.matchpoints = matchpoints or [
            "oclc_number",
            "isbn",
            "issn",
            "bib_id",
            "upc",
        ]

    def _select_best_match(
        self, bib_to_match: model.DomainBib, candidates: List[Dict[str, Any]]
    ) -> Optional[str]:
        max_matched_points = -1
        best_match_bib_id = None
        for bib in candidates:
            matched_points = 0
            for attr in self.matchpoints:
                if getattr(bib_to_match, attr) == bib.get(attr):
                    matched_points += 1

            if matched_points > max_matched_points:
                max_matched_points = matched_points
                best_match_bib_id = bib.get("bib_id")

        return best_match_bib_id

    def find_best_match(self, bib: model.DomainBib) -> Optional[str]:
        for key in self.matchpoints:
            value = getattr(bib, key, None)
            if not value:
                continue
            candidates = self.fetcher.get_bibs_by_id(value=value, key=key)
            if candidates:
                return self._select_best_match(bib_to_match=bib, candidates=candidates)
        return None
