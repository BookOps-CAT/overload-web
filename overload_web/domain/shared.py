from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Collection(StrEnum):
    """Valid values for NYPL and BPL collections"""

    BRANCH = "BL"
    RESEARCH = "RL"
    MIXED = "MIXED"
    NONE = "NONE"


class LibrarySystem(StrEnum):
    """Valid values for library system"""

    BPL = "bpl"
    NYPL = "nypl"


class RecordType(StrEnum):
    """Valid values for record type/processing workflow."""

    ACQUISITIONS = "acq"
    CATALOGING = "cat"
    SELECTION = "sel"


@dataclass(frozen=True)
class ParsedSubfield:
    """A pure Python representation of a MARC subfield."""

    code: str
    value: str


class ParsedField:
    def __init__(
        self,
        tag: str,
        indicators: tuple[str, str] | None = None,
        subfields: list[ParsedSubfield] | list[dict[str, str]] = [],
        value: str | None = None,
    ):
        self.tag = tag
        self.indicators = indicators
        self.subfields = [
            i if isinstance(i, ParsedSubfield) else ParsedSubfield(**i)
            for i in subfields
        ]
        self.value = value
