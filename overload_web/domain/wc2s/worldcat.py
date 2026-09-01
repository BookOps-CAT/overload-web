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
    MATCHED = "matched"
    FAILED_GLOBAL_CRITERIA = "global"
    FAILED_USER_CRITERIA = "user"


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
class UpgradeItem:
    id: str
    id_type: IdType
    status: MatchStatus
    matched_oclc: str | None = None


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
    required_cat_agency: Literal["DLC"] | None = None
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
        out = []
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

    def filter_brief_bibs(
        self, responses: list[BriefRecordResult], source: SourceData
    ) -> list[UpgradeItem]:
        out = []
        for response in responses:
            print(source.update_datetime)
            print(response.update_datetime)
            if (
                source.update_datetime
                and response.update_datetime
                and source.update_datetime > response.update_datetime
            ):
                out.append(
                    UpgradeItem(
                        id=source.id,
                        id_type=source.id_type,
                        status=MatchStatus.FAILED_GLOBAL_CRITERIA,
                        matched_oclc=response.oclc_number,
                    )
                )
            elif response.cat_level not in self.valid_cat_levels:
                out.append(
                    UpgradeItem(
                        id=source.id,
                        id_type=source.id_type,
                        status=MatchStatus.FAILED_USER_CRITERIA,
                        matched_oclc=response.oclc_number,
                    )
                )
            else:
                out.append(
                    UpgradeItem(
                        id=source.id,
                        id_type=source.id_type,
                        status=MatchStatus.MATCHED,
                        matched_oclc=response.oclc_number,
                    )
                )
        return out
