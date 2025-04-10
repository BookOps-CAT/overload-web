from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass
from typing import List, Optional, Union


@dataclass
class DomainBib:
    library: str
    orders: List[Order]
    bib_id: Optional[str] = None
    isbn: Optional[str] = None
    oclc_number: Optional[Union[str, List[str]]] = None
    upc: Optional[str] = None

    def match(self, bibs: List[DomainBib], matchpoints: List[str]) -> None:
        max_matched_points = -1
        best_match_bib_id = None
        for bib in bibs:
            matched_points = 0
            for attr in matchpoints:
                if getattr(self, attr) == getattr(bib, attr):
                    matched_points += 1

            if matched_points > max_matched_points:
                max_matched_points = matched_points
                best_match_bib_id = bib.bib_id
        self.bib_id = best_match_bib_id


@dataclass
class Order:
    audience: Optional[str]
    blanket_po: Optional[str]
    copies: Optional[Union[str, int]]
    country: Optional[str]
    create_date: Optional[Union[datetime.datetime, datetime.date, str]]
    format: Optional[str]
    fund: Optional[str]
    internal_note: Optional[str]
    lang: Optional[str]
    locations: List[str]
    order_type: Optional[str]
    price: Optional[Union[str, int]]
    selector: Optional[str]
    selector_note: Optional[str]
    source: Optional[str]
    status: Optional[str]
    var_field_isbn: Optional[str]
    vendor_code: Optional[str]
    vendor_notes: Optional[str]
    vendor_title_no: Optional[str]

    def apply_template(self, template: Template) -> None:
        template_dict = asdict(template)
        for k, v in template_dict.items():
            if k in asdict(self).keys():
                setattr(self, k, v)


@dataclass(kw_only=True)
class Template:
    agent: Optional[str] = None
    audience: Optional[str] = None
    blanket_po: Optional[str] = None
    copies: Optional[Union[str, int]] = None
    country: Optional[str] = None
    create_date: Optional[Union[datetime.datetime, datetime.date, str]] = None
    format: Optional[str] = None
    fund: Optional[str] = None
    id: Optional[str] = None
    internal_note: Optional[str] = None
    lang: Optional[str] = None
    order_type: Optional[str] = None
    name: Optional[str] = None
    price: Optional[Union[str, int]] = None
    selector: Optional[str] = None
    selector_note: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    var_field_isbn: Optional[str] = None
    vendor_code: Optional[str] = None
    vendor_notes: Optional[str] = None
    vendor_title_no: Optional[str] = None

    primary_matchpoint: Optional[str] = None
    secondary_matchpoint: Optional[str] = None
    tertiary_matchpoint: Optional[str] = None

    @property
    def matchpoints(self) -> List[str]:
        return [
            i
            for i in [
                self.primary_matchpoint,
                self.secondary_matchpoint,
                self.tertiary_matchpoint,
            ]
            if i
        ]
