"""Dependency injection functions."""

from __future__ import annotations

import logging
from typing import Annotated, Literal

from fastapi import Depends, Form, UploadFile
from pydantic import BaseModel, field_validator

from overload_web.infrastructure import marc_handler, oclc

logger = logging.getLogger(__name__)


class UserCriteria(BaseModel):
    id_type: Literal["isbn", "issn", "lccn", "upc", "oclc_number"]
    library: Literal["nypl", "bpl"]
    collection: Literal["BL", "RL", ""] | None
    material_type: Literal["any", "bluray", "dvd", "large_print", "print"]
    action: Literal["catalog", "upgrade"]
    record_level: Literal["1", "2", "3"]
    cat_agency: Literal["DLC", "any"] | None = None
    cat_rules: Literal["RDA", "any"] | None = None
    data_source: str | None = None

    @field_validator("collection", mode="before")
    @classmethod
    def parse_collection(
        cls, value: Literal["BL", "RL"] | None
    ) -> Literal["BL", "RL"] | None:
        """Parses value of `collection` param from html forms."""
        if not value:
            return None
        else:
            return value

    @classmethod
    def from_form(
        self,
        id_type: Literal["isbn", "issn", "lccn", "upc", "oclc_number"] = Form(...),
        record_level: Literal["1", "2", "3"] = Form(...),
        library: Literal["nypl", "bpl"] = Form(...),
        collection: Literal["BL", "RL", ""] | None = Form(None),
        material_type: Literal["any", "bluray", "dvd", "large_print", "print"] = Form(
            default="any"
        ),
        action: Literal["catalog", "upgrade"] = Form(default="catalog"),
        cat_agency: Literal["DLC", "any"] | None = Form(default=None),
        cat_rules: Literal["RDA", "any"] | None = Form(default=None),
        data_source: Literal["id", "export"] | None = Form(default="id"),
    ) -> UserCriteria:
        return UserCriteria(
            id_type=id_type,
            library=library,
            collection=collection,
            material_type=material_type,
            action=action,
            record_level=record_level,
            cat_agency=cat_agency,
            cat_rules=cat_rules,
            data_source=data_source,
        )


class SourceDataModel(BaseModel):
    id: str
    id_type: Literal["isbn", "issn", "lccn", "upc", "oclc_number"]
    library: Literal["nypl", "bpl"]
    collection: Literal["BL", "RL", ""] | None
    material_type: Literal["any", "bluray", "dvd", "large_print", "print"]
    action: Literal["catalog", "upgrade"]
    record_level: Literal["1", "2", "3"]
    required_cataloging_agency: Literal["DLC", "any"] | None = None
    required_cataloging_rules: Literal["RDA", "any"] | None = None
    update_date: str | None = None


def get_marc_parser() -> marc_handler.MarcParser:
    """Create a `MarcParser` service with injected dependencies."""
    return marc_handler.MarcParser()


def oclc_fetcher(
    user_criteria: Annotated[UserCriteria, Depends(UserCriteria.from_form)],
) -> oclc.WorldcatFetcher:
    return oclc.WorldcatFetcher(session=oclc.OclcSession(library=user_criteria.library))


def load_wc2s_file(file: UploadFile) -> list[str]:
    lines = file.file.readlines()
    return [i.decode("utf-8").strip("\r\n") for i in lines]


def source_data_from_load(
    ids: Annotated[list[str], Depends(load_wc2s_file)],
    data: Annotated[UserCriteria, Depends(UserCriteria.from_form)],
) -> list:
    return [
        SourceDataModel(
            id=i,
            id_type=data.id_type,
            library=data.library,
            collection=data.collection,
            material_type=data.material_type,
            action=data.action,
            record_level=data.record_level,
            required_cataloging_agency=data.cat_agency,
            required_cataloging_rules=data.cat_rules,
        )
        for i in ids
    ]
