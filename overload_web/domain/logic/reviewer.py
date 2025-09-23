from typing import Any

from overload_web.domain import models


class ReviewedResults:
    def __init__(
        self,
        input: models.bibs.DomainBib,
        results: list[models.responses.FetcherResponseDict],
        record_type: models.bibs.RecordType,
    ) -> None:
        self.input = input
        self.results = results
        self.vendor = input.vendor
        self.target_bib_id = input.bib_id
        self.record_type = record_type
        self.action = None

        self.matched_results: list[models.responses.FetcherResponseDict] = []
        self.mixed_results: list[models.responses.FetcherResponseDict] = []
        self.other_results: list[models.responses.FetcherResponseDict] = []

        self._sort_results()

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


class BibReviewer:
    def __init__(self, rules: dict[str, Any]) -> None:
        self.rules = rules

    def review_results(
        self,
        input: models.bibs.DomainBib,
        results: list[models.responses.FetcherResponseDict],
        record_type: models.bibs.RecordType,
    ) -> ReviewedResults:
        reviewed_results = ReviewedResults(
            input=input, results=results, record_type=record_type
        )
        return reviewed_results
