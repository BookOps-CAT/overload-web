from __future__ import annotations

from overload_web.bib_records.domain import bibs


class ReviewedResults:
    """
    Compare a `DomainBib` to a list of candidate bibs and select the best match.

    Args:
        input: the bib record to match as a `DomainBib`.
        results: a list of candidate bib records as dicts
        record_type: the type of record as an enum (either `FULL` or `ORDER_LEVEL`)

    Returns:
        The results as a `bibs.ReviewedResults` object.
    """

    def __init__(
        self,
        record_type: str,
    ) -> None:
        self.record_type = record_type

    def _sort_results(self) -> None:
        sorted_results = sorted(
            self.results, key=lambda i: int(i["bib_id"].strip(".b"))
        )
        for result in sorted_results:
            if result["collection"] == "MIXED":
                self.mixed_results.append(result)
            elif result["collection"] == str(self.input.collection):
                self.matched_results.append(result)
            else:
                self.other_results.append(result)

    def review_results(
        self, input: bibs.DomainBib, results: list[bibs.FetcherResponseDict]
    ) -> str | None:
        self.input = input
        self.results = results
        self.vendor = input.vendor

        self.action = None

        self.matched_results: list[bibs.FetcherResponseDict] = []
        self.mixed_results: list[bibs.FetcherResponseDict] = []
        self.other_results: list[bibs.FetcherResponseDict] = []

        self._sort_results()
        return self.target_bib_id

    @property
    def duplicate_records(self) -> list[str]:
        duplicate_records: list[str] = []
        if len(self.matched_results) > 1:
            return [i["bib_id"] for i in self.matched_results]
        return duplicate_records

    @property
    def input_call_no(self) -> str | None:
        if str(self.input.collection) == "RL":
            call_no = self.input.research_call_number
            return call_no[0] if isinstance(call_no, list) else call_no
        elif str(self.input.collection) == "BL":
            call_no = self.input.branch_call_number
            return call_no[0] if isinstance(call_no, list) else call_no
        elif str(self.input.library) == "BPL":
            call_no = self.input.branch_call_number
            return call_no[0] if isinstance(call_no, list) else call_no
        return None

    @property
    def resource_id(self) -> str | None:
        if self.input.bib_id:
            return str(self.input.bib_id)
        elif self.input.control_number:
            return self.input.control_number
        elif self.input.isbn:
            return self.input.isbn
        elif self.input.oclc_number:
            return (
                self.input.oclc_number
                if isinstance(self.input.oclc_number, str)
                else self.input.oclc_number[0]
            )
        elif self.input.upc:
            return self.input.upc
        return None

    @property
    def target_bib_id(self) -> str | None:
        bib_id = None
        if len(self.matched_results) == 1:
            return self.matched_results[0]["bib_id"]
        elif len(self.matched_results) == 0:
            return bib_id
        for result in self.matched_results:
            if result.get("branch_call_number") or result.get("research_call_number"):
                return result["bib_id"]
        return bib_id
