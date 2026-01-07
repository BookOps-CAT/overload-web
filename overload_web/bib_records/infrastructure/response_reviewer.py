from __future__ import annotations

import logging

from overload_web.bib_records.domain import bibs, marc_protocols

logger = logging.getLogger(__name__)


class ReviewStrategyFactory:
    def make(
        self, library: str, record_type: str, collection: str
    ) -> marc_protocols.BibReviewStrategy:
        match record_type, library, collection:
            case "cat", "nypl", "BL":
                return NYPLCatBranchReviewStrategy()
            case "cat", "nypl", "RL":
                return NYPLCatResearchReviewStrategy()
            case "cat", "bpl", _:
                return BPLCatReviewStrategy()
            case "acq", _, _:
                return AcquisitionsReviewStrategy()
            case "sel", _, _:
                return SelectionReviewStrategy()
            case _:
                raise ValueError("Invalid library/record_type/collection combination")


class BaseReviewStrategy:
    """
    Compare a `DomainBib` to a list of candidate bibs and select the best match.

    Args:
        None

    Returns:
        The results as a `bibs.ReviewedResults` object.
    """

    def __init__(self) -> None:
        self.input: bibs.DomainBib
        self.results: list[bibs.BaseSierraResponse]
        self.vendor: str | None
        self.call_number_match: bool
        self.action: str | None = None

        self.matched_results: list[bibs.BaseSierraResponse] = []
        self.mixed_results: list[bibs.BaseSierraResponse] = []
        self.other_results: list[bibs.BaseSierraResponse] = []

    @property
    def duplicate_records(self) -> list[str]:
        duplicate_records: list[str] = []
        if len(self.matched_results) > 1:
            return [i.bib_id for i in self.matched_results]
        return duplicate_records

    @property
    def input_call_no(self) -> str | None:
        call_no = None
        if str(self.input.library) == "nypl" and str(self.input.collection) == "RL":
            call_no = self.input.research_call_number
        else:
            call_no = self.input.branch_call_number
        if isinstance(call_no, list):
            return call_no[0]
        return call_no

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
        return self._target_bib_id

    @target_bib_id.setter
    def target_bib_id(self, id: str | None) -> None:
        self._target_bib_id = id

    def compare_branch_call_nos(
        self,
        input_call_no: str | None,
        result_call_no: str | None,
    ) -> bool:
        return input_call_no == result_call_no

    def sort_results(
        self, input: bibs.DomainBib, results: list[bibs.BaseSierraResponse]
    ) -> None:
        self.input = input
        self.results = results
        self.vendor = input.vendor

        sorted_results = sorted(self.results, key=lambda i: int(i.bib_id.strip(".b")))
        for result in sorted_results:
            if result.library == "bpl":
                self.matched_results.append(result)
            elif result.collection == "MIXED":
                self.mixed_results.append(result)
            elif str(result.collection) == str(self.input.collection):
                self.matched_results.append(result)
            else:
                self.other_results.append(result)
        self.target_bib_id = self.input.bib_id


class SelectionReviewStrategy(BaseReviewStrategy):
    def review_results(
        self, input: bibs.DomainBib, results: list[bibs.BaseSierraResponse]
    ) -> str | None:
        self.sort_results(input=input, results=results)

        self.action = None
        self.call_number_match = True
        if len(self.matched_results) > 0:
            for result in self.matched_results:
                if (
                    result.branch_call_number is not None
                    or len(result.research_call_number) > 0
                ):
                    self.action = "attach"
                    self.target_bib_id = result.bib_id
                    break
            if self.action is None:
                self.action = "attach"
                self.target_bib_id = result.bib_id

        return self.target_bib_id


class AcquisitionsReviewStrategy(BaseReviewStrategy):
    def review_results(
        self, input: bibs.DomainBib, results: list[bibs.BaseSierraResponse]
    ) -> str | None:
        self.sort_results(input=input, results=results)
        self.call_number_match = True
        self.action = "insert"
        return self.target_bib_id


class NYPLCatResearchReviewStrategy(BaseReviewStrategy):
    def review_results(
        self, input: bibs.DomainBib, results: list[bibs.BaseSierraResponse]
    ) -> str | None:
        self.sort_results(input=input, results=results)
        if len(self.matched_results) == 0:
            self.call_number_match = True
        else:
            self.call_number_match = False
        for result in self.matched_results:
            if result.research_call_number:
                self.call_number_match = True
                self.target_bib_id = result.bib_id
                self.target_title = result.title
                self.target_call_number = result.research_call_number
                if result.cat_source == "inhouse":
                    self.action = "attach"
                else:
                    if (
                        not self.input.update_datetime
                        or result.update_datetime > self.input.update_datetime
                    ):
                        self.updated_by_vendor = True
                        self.action = "overlay"
                    else:
                        self.action = "attach"
                break
        if not self.call_number_match:
            self.target_bib_id = self.matched_results[-1].bib_id
            self.target_title = self.matched_results[-1].title
            self.action = "overlay"

        return self.target_bib_id


class NYPLCatBranchReviewStrategy(BaseReviewStrategy):
    def review_results(
        self, input: bibs.DomainBib, results: list[bibs.BaseSierraResponse]
    ) -> str | None:
        self.sort_results(input=input, results=results)
        if len(self.matched_results) == 0:
            self.call_number_match = True
        else:
            self.call_number_match = False
        for result in self.matched_results:
            if result.branch_call_number:
                call_match = self.compare_branch_call_nos(
                    input_call_no=self.input.branch_call_number,
                    result_call_no=result.branch_call_number,
                )
                if call_match:
                    self.call_number_match = True
                    self.target_bib_id = result.bib_id
                    self.target_title = result.title
                    self.target_call_number = result.branch_call_number
                    if result.cat_source == "inhouse":
                        self.action = "attach"
                    else:
                        if (
                            not self.input.update_datetime
                            or result.update_datetime > self.input.update_datetime
                        ):
                            self.updated_by_vendor = True
                            self.action = "overlay"
                        else:
                            self.action = "attach"
                    break
        if self.call_number_match:
            return self.target_bib_id
        if self.matched_results[-1].branch_call_number is not None:
            self.target_bib_id = result.bib_id
            self.target_title = result.title
            self.target_call_number = self.matched_results[-1].branch_call_number
            if result.cat_source == "inhouse":
                self.action = "attach"
            else:
                if (
                    not self.input.update_datetime
                    or result.update_datetime > self.input.update_datetime
                ):
                    self.updated_by_vendor = True
                    self.action = "overlay"
                else:
                    self.action = "attach"
        else:
            self.target_bib_id = self.matched_results[-1].bib_id
            self.target_title = self.matched_results[-1].title
            self.action = "overlay"
        return self.target_bib_id


class BPLCatReviewStrategy(BaseReviewStrategy):
    def review_results(
        self, input: bibs.DomainBib, results: list[bibs.BaseSierraResponse]
    ) -> str | None:
        self.sort_results(input=input, results=results)
        if len(self.matched_results) == 0:
            self.call_number_match = True
            if self.vendor in ["Midwest DVD", "Midwest Audio", "Midwest CD"]:
                self.action = "attach"
        else:
            self.call_number_match = False
        for result in self.matched_results:
            if result.branch_call_number:
                call_match = self.compare_branch_call_nos(
                    input_call_no=self.input.branch_call_number,
                    result_call_no=result.branch_call_number,
                )
                if call_match:
                    self.call_number_match = True
                    self.target_bib_id = result.bib_id
                    self.target_title = result.title
                    self.target_call_number = result.branch_call_number
                    if result.cat_source == "inhouse":
                        self.action = "attach"
                    else:
                        if (
                            not self.input.update_datetime
                            or result.update_datetime > self.input.update_datetime
                        ):
                            self.updated_by_vendor = True
                            self.action = "overlay"
                        else:
                            self.action = "attach"
                    break
        if self.call_number_match:
            return self.target_bib_id
        if self.matched_results[-1].branch_call_number is not None:
            self.target_bib_id = result.bib_id
            self.target_title = result.title
            self.target_call_number = self.matched_results[-1].branch_call_number
            if result.cat_source == "inhouse":
                self.action = "attach"
            else:
                if (
                    not self.input.update_datetime
                    or result.update_datetime > self.input.update_datetime
                ):
                    self.updated_by_vendor = True
                    self.action = "overlay"
                else:
                    self.action = "attach"
        else:
            self.target_bib_id = self.matched_results[-1].bib_id
            self.target_title = self.matched_results[-1].title
            self.action = "overlay"
        return self.target_bib_id
