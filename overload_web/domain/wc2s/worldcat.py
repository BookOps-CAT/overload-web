from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal

from overload_web.domain.shared import context


class Action(StrEnum):
    CATALOG = "catalog"
    UPGRADE = "upgrade"


class IdType(StrEnum):
    ISBN = "isbn"
    ISSN = "issn"
    LCCN = "lccn"
    OCLC_NUMBER = "oclc_number"
    UPC = "upc"


class MatchStatus(StrEnum):
    FAILED_GLOBAL_CRITERIA = "global"
    FAILED_USER_CRITERIA = "user"
    MATCHED = "matched"


class MaterialType(StrEnum):
    ANY = "any"
    BLURAY = "bluray"
    DVD = "dvd"
    LARGE_PRINT = "large_print"
    PRINT = "print"


@dataclass(kw_only=True)
class BriefRecordResult:
    """A domain model for a brief bib response from a Worldcat2Sierra query."""

    cat_agency: str
    cat_language: str
    cat_level: str
    creator: str
    date: str
    language: str
    merged_oclc_numbers: list[str]
    oclc_number: str
    title: str
    edition: str | None = None
    format: str | None = None
    isbns: list[str] | None = None
    issns: list[str] | None = None
    publisher: str | None = None
    pub_place: str | None = None
    update_date: str | None = None

    @property
    def update_datetime(self) -> datetime.datetime | None:
        """Creates `datetime.datetime` object from `update_date` string."""
        if self.update_date:
            return datetime.datetime.strptime(self.update_date, "%y%m%d")
        return None


@dataclass
class MatchedItem:
    id: str
    id_type: IdType
    status: MatchStatus
    matched_oclc: str


@dataclass
class MatchedResult:
    matched: bool
    source_data: SourceData
    failed_matches: list[MatchedItem] | None = None
    successful_matches: list[MatchedItem] | None = None


@dataclass
class SourceData:
    """A domain model representing a Worldcat2Sierra query."""

    collection: context.Collection | None
    id: str
    id_type: IdType
    library: context.LibrarySystem
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
    CAT_LEVELS = {
        "1": [" ", "I", "4"],
        "2": [" ", "I", "4", "M", "K", "7", "1", "2"],
        "3": [" ", "I", "4", "M", "K", "7", "1", "2", "3", "8"],
    }

    def __init__(self, record_level: str) -> None:
        self.record_level = record_level

    @property
    def valid_cat_levels(self) -> list[str]:
        return self.CAT_LEVELS[self.record_level]

    def parse_responses(
        self, responses: list[dict[str, Any]]
    ) -> list[BriefRecordResult]:
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
                merged_oclc_numbers=record["mergedOclcNumbers"],
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
    ) -> MatchedResult:
        if not responses:
            return MatchedResult(matched=False, source_data=source)
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
        return MatchedResult(
            matched=True,
            source_data=source,
            failed_matches=failed_matches,
            successful_matches=success,
        )
