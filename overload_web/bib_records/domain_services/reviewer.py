from __future__ import annotations

from overload_web.bib_records.domain import bibs
from overload_web.bib_records.infrastructure import sierra_responses


class ReviewedResults:
    """
    Compare a `DomainBib` to a list of candidate bibs and select the best match.

    Args:
        None

    Returns:
        The results as a `bibs.ReviewedResults` object.
    """

    def __init__(self) -> None:
        self.input: bibs.DomainBib
        self.results: list[sierra_responses.BaseSierraResponse]
        self.vendor: str | None
        self.call_number_match: bool
        self.action: str | None = None

        self.matched_results: list[sierra_responses.BaseSierraResponse] = []
        self.mixed_results: list[sierra_responses.BaseSierraResponse] = []
        self.other_results: list[sierra_responses.BaseSierraResponse] = []

    def _sort_results(self) -> None:
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

    def review_results(
        self,
        input: bibs.DomainBib,
        results: list[sierra_responses.BaseSierraResponse],
        record_type: bibs.RecordType,
    ) -> str | None:
        self.input = input
        self.results = results
        self.vendor = input.vendor

        self.action = None

        self._sort_results()
        self.target_bib_id = self.input.bib_id
        if (
            record_type == bibs.RecordType.CATALOGING
            and self.input.library == bibs.LibrarySystem.BPL
        ):
            self._cataloging_bpl_workflow()
        elif (
            record_type == bibs.RecordType.CATALOGING
            and self.input.collection == bibs.Collection.BRANCH
        ):
            self._cataloging_bl_workflow()
        elif (
            record_type == bibs.RecordType.CATALOGING
            and self.input.collection == bibs.Collection.RESEARCH
        ):
            self._cataloging_rl_workflow()
        elif record_type == bibs.RecordType.SELECTION:
            self._selection_workflow()
        elif record_type == bibs.RecordType.ACQUISITIONS:
            self._acquisition_workflow()
        return self.target_bib_id

    def _compare_call_nos(
        self,
        input_call_no: str | list[str] | None,
        result_call_no: str | list[str] | None,
    ) -> bool:
        if isinstance(input_call_no, str):
            input_call_no = [input_call_no]
        if isinstance(result_call_no, str):
            result_call_no = [result_call_no]
        return input_call_no == result_call_no

    def _cataloging_bl_workflow(self):
        # default action = 'insert'
        if not self.matched_results:
            self.call_number_match = True
        else:
            self.call_number_match = False
        for result in self.matched_results:
            # full record scenario
            if result.branch_call_number:
                # check if call number matches
                call_match = self._compare_call_nos(
                    result.branch_call_number, self.input.branch_call_number
                )
                if call_match:
                    self.call_number_match = True
                    self.target_bib_id = result.bib_id
                    self.target_title = result.title
                    self.target_call_number = result.branch_call_number
                    if result.cat_source == "inhouse":
                        self.action = "attach"
                    else:
                        updated = result.update_date > self.input.update_date
                        if updated:
                            self.updated_by_vendor = True
                            self.action = "overlay"
                        else:
                            self.action = "attach"
                    break

        if not self.call_number_match and self.matched_results[-1].branch_call_number:
            self.target_bib_id = result.bib_id
            self.target_title = result.title
            self.target_call_number = result.branch_call_number
            if result.cat_source == "inhouse":
                self.action = "attach"
            else:
                updated = result.update_date > self.input.update_date
                if updated:
                    self.updated_by_vendor = True
                    self.action = "overlay"
                else:
                    self.action = "attach"
        if not self.call_number_match:
            self.call_number_match = True
            self.target_bib_id = self.matched_results[-1].bib_id
            self.target_title = self.matched_results[-1].title
            self.action = "overlay"

    def _cataloging_bpl_workflow(self):
        # default action = 'insert'
        if not self.matched_results:
            self.call_number_match = True
            if self.vendor in ["Midwest DVD", "Midwest Audio", "Midwest CD"]:
                self.action = "attach"
        else:
            self.call_number_match = False
        for result in self.matched_results:
            # full record scenario
            if result.branch_call_number:
                # check if call number matches
                call_match = self._compare_call_nos(
                    result.branch_call_number, self.input.branch_call_number
                )
                if call_match:
                    self.call_number_match = True
                    self.target_bib_id = result.bib_id
                    self.target_title = result.title
                    self.target_call_number = result.branch_call_number
                    if result.cat_source == "inhouse":
                        self.action = "attach"
                    else:
                        updated = result.update_date > self.input.update_date
                        if updated:
                            self.updated_by_vendor = True
                            self.action = "overlay"
                        else:
                            self.action = "attach"
                    break
        if not self.call_number_match and self.matched_results[-1].branch_call_number:
            self.target_bib_id = result.bib_id
            self.target_title = result.title
            self.target_call_number = result.branch_call_number
            if result.cat_source == "inhouse":
                self.action = "attach"
            else:
                updated = result.update_date > self.input.update_date
                if updated:
                    self.updated_by_vendor = True
                    self.action = "overlay"
                else:
                    self.action = "attach"
        if not self.call_number_match:
            self.call_number_match = True
            self.target_bib_id = self.matched_results[-1].bib_id
            self.target_title = self.matched_results[-1].title
            self.action = "overlay"

    def _cataloging_rl_workflow(self):
        # default action = 'insert'
        self.call_number_match = False
        if not self.matched_results:
            self.call_number_match = True
        for result in self.matched_results:
            # full record scenario
            if result.research_call_number:
                # research path, no call_number match checking
                self.call_number_match = True
                # set_target_id
                self.target_bib_id = result.bib_id
                self.target_title = result.title
                self.target_call_number = result.research_call_number
                if result.cat_source == "inhouse":
                    self.action = "attach"
                else:
                    updated = result.update_date > self.input.update_date
                    if updated:
                        self.updated_by_vendor = True
                        self.action = "overlay"
                    else:
                        self.action = "attach"
                break
        if not self.call_number_match:
            self.call_number_match = True
            self.target_bib_id = self.matched_results[-1].bib_id
            self.target_title = self.matched_results[-1].title
            self.action = "overlay"

    def _selection_workflow(self):
        # default action = 'insert'
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

    def _acquisition_workflow(self):
        self.call_number_match = True
        self.action = "insert"

    @property
    def duplicate_records(self) -> list[str]:
        duplicate_records: list[str] = []
        if len(self.matched_results) > 1:
            return [i.bib_id for i in self.matched_results]
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
        return self._target_bib_id

    @target_bib_id.setter
    def target_bib_id(self, id: str | None) -> None:
        self._target_bib_id = id
