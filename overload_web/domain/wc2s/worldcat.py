"""Domain services for the Worldcat2Sierra application."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal

from overload_web.domain import shared


class Action(StrEnum):
    """Whether the record should be upgraded or just cataloged."""

    CATALOG = "catalog"
    UPGRADE = "upgrade"


class IdType(StrEnum):
    """The type of identifier being used in a search."""

    ISBN = "isbn"
    ISSN = "issn"
    LCCN = "lccn"
    OCLC_NUMBER = "oclc_number"
    UPC = "upc"


class MatchStatus(StrEnum):
    """The result of a Metadata API search and review of the returned matches."""

    FAILED_GLOBAL_CRITERIA = "global"
    FAILED_USER_CRITERIA = "user"
    MATCHED = "matched"


class MaterialType(StrEnum):
    """The target material type for any matched MARC records."""

    ANY = "any"
    BLURAY = "bluray"
    DVD = "dvd"
    LARGE_PRINT = "large_print"
    PRINT = "print"


class BriefRecordResult:
    """A domain model for a brief bib response from a Worldcat2Sierra query."""

    def __init__(
        self,
        cat_agency: str,
        cat_language: str,
        cat_level: str,
        creator: str,
        date: str,
        language: str,
        merged_oclc_numbers: list[str],
        oclc_number: str,
        title: str,
        edition: str | None = None,
        format: str | None = None,
        isbns: list[str] | None = None,
        issns: list[str] | None = None,
        publisher: str | None = None,
        pub_place: str | None = None,
        update_datetime: datetime.datetime | None = None,
    ) -> None:
        """Initialize a `BriefRecordResult` instance.

        Args:
            cat_agency: the institution who created the catalog record as a string.
            cat_language: the language of cataloging as a string.
            cat_level: the level of cataloging as a string.
            creator: the creator from the MARC record as a string.
            date: the publication date from the MARC record as a string.
            language: the language of the material as a string.
            merged_oclc_numbers: a list of previously used OCLC numbers for the record.
            oclc_number: the current OCLC number for the record as a string.
            title: the title of the material as a string.
            edition: the edition statement from the MARC record, if present.
            format: the format from the MARC record, if present.
            isbns: a list of ISBNs associated with the material, if present.
            issns: a list of ISSNs associated with the material, if present.
            publisher: the publisher of the material, if present.
            pub_place: the place of publication of the material, if present.
            update_datetime: the date of publication, if present, as a datetime obj.

        """
        self.cat_agency = cat_agency
        self.cat_language = cat_language
        self.cat_level = cat_level
        self.creator = creator
        self.date = date
        self.language = language
        self.merged_oclc_numbers = merged_oclc_numbers
        self.oclc_number = oclc_number
        self.title = title
        self.edition = edition
        self.format = format
        self.isbns = isbns
        self.issns = issns
        self.publisher = publisher
        self.pub_place = pub_place
        self.update_datetime = update_datetime

    @property
    def update_datetime(self) -> datetime.datetime | None:
        """Last update of record as a string."""
        return self._update_datetime

    @update_datetime.setter
    def update_datetime(self, value: str | None) -> None:
        """Create `datetime.datetime` object from a string."""
        if value:
            self._update_datetime = datetime.datetime.strptime(value, "%y%m%d")


@dataclass
class MatchedItem:
    """A record matched that successfully matched successfully by WC2Sierra."""

    id: str
    id_type: IdType
    status: MatchStatus
    matched_oclc: str


@dataclass
class MatchedResultBrief:
    """A record matched that successfully matched successfully by WC2Sierra."""

    matched: bool
    failed_matches: list[MatchedItem]
    successful_matches: list[MatchedItem]


@dataclass
class FullMatchedItem(MatchedItem):
    """A full MARC record for a matched record."""

    full_record: bytes | Any


@dataclass
class MatchedResultFull:
    """All matches, failed matches, and source data used within a workflow."""

    matched: bool
    failed_matches: list[MatchedItem]
    successful_matches: list[MatchedItem]
    full_record_matches: list[FullMatchedItem]
    source_data: SourceData


@dataclass
class SourceData:
    """A domain model representing a Worldcat2Sierra query."""

    collection: shared.Collection | None
    id: str
    id_type: IdType
    library: shared.LibrarySystem
    material_type: MaterialType
    action: Action
    record_level: str
    required_cataloging_agency: Literal["DLC"] | None = None
    required_cataloging_rules: Literal["RDA"] | None = None
    update_date: str | None = None

    @property
    def update_datetime(self) -> datetime.datetime | None:
        """Creates `datetime.datetime` object from `update_date` string."""
        if self.update_date:
            return datetime.datetime.strptime(self.update_date, "%Y%m%d%H%M%S.%f")
        return None


class RecordEvaluator:
    """Evaluates the results returned by queries to the Metadata API."""

    CAT_LEVELS = {
        "1": [" ", "I", "4"],
        "2": [" ", "I", "4", "M", "K", "7", "1", "2"],
        "3": [" ", "I", "4", "M", "K", "7", "1", "2", "3", "8"],
    }

    def __init__(self, record_level: str) -> None:
        """Initialize a `RecordEvaluator` object.

        Args:
            record_level: the level of cataloging required for successful matches.

        """
        self.record_level = record_level

    @property
    def valid_cat_levels(self) -> list[str]:
        """Cataloging levels (Leader[17]) that would be valid for successful matches."""
        return self.CAT_LEVELS[self.record_level]

    def parse_responses(
        self, responses: list[dict[str, Any]]
    ) -> list[BriefRecordResult]:
        """Parse a list of json responses returned from the Metadata API.

        Args:
            responses:
                a list of dictionaries representing brief bib responses from
                the Metadata API.

        Returns:
            a list of parsed responses as `BriefRecordResult` objects

        """
        out: list[BriefRecordResult] = []
        if not responses:
            return out
        for record in responses:
            cat_info = record["catalogingInfo"]
            parsed = BriefRecordResult(
                cat_agency=cat_info["catalogingAgency"],
                cat_language=cat_info["catalogingLanguage"],
                cat_level=cat_info["levelOfCataloging"],
                creator=record["creator"],
                date=record["date"],
                language=record["language"],
                merged_oclc_numbers=record.get("mergedOclcNumbers", []),
                oclc_number=record["oclcNumber"],
                title=record["title"],
                edition=record.get("edition"),
                format=record.get("specificFormat", record.get("generalFormat")),
                isbns=record.get("isbns"),
                issns=record.get("issns"),
                publisher=record.get("publisher"),
                pub_place=record.get("pub_place"),
            )
            out.append(parsed)
        return out

    def filter_brief_bib_matches(
        self, responses: list[BriefRecordResult], source: SourceData
    ) -> MatchedResultBrief:
        """Review brief bib responses against evaluation criteria.

        Args:
            responses: a list of responses from OCLC as `BriefRecordResult` objects
            source: a `SourceData` object representing user-supplied evaluation criteria
        Returns:
            The results of the evaluation wrapped in a `MatchedResultBrief` object.

        """
        if not responses:
            return MatchedResultBrief(
                matched=False, failed_matches=[], successful_matches=[]
            )
        success = []
        failed_matches = []
        for response in responses:
            if response.cat_level not in self.valid_cat_levels:
                status = MatchStatus.FAILED_USER_CRITERIA

            elif source.action == Action.UPGRADE and (
                not response.update_datetime or not source.update_datetime
            ):
                status = MatchStatus.FAILED_GLOBAL_CRITERIA
            elif (
                source.action == Action.UPGRADE
                and response.update_datetime
                and source.update_datetime
                and source.update_datetime > response.update_datetime
            ):
                status = MatchStatus.FAILED_GLOBAL_CRITERIA
            else:
                status = MatchStatus.MATCHED
            item = MatchedItem(
                id=source.id,
                id_type=source.id_type,
                status=status,
                matched_oclc=response.oclc_number,
            )
            if status == "matched":
                success.append(item)
            else:
                failed_matches.append(item)
        return MatchedResultBrief(
            matched=True, failed_matches=failed_matches, successful_matches=success
        )
