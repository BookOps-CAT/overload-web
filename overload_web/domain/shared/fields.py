from __future__ import annotations

from dataclasses import dataclass


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
