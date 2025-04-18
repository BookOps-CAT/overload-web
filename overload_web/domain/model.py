from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class DomainBib:
    library: str
    orders: List[Order]
    bib_id: Optional[str] = None
    isbn: Optional[str] = None
    oclc_number: Optional[Union[str, List[str]]] = None
    upc: Optional[str] = None

    def apply_template(self, template_data: Dict[str, Any]) -> None:
        for order in self.orders:
            order.apply_template(template_data=template_data)

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
class Matchpoints:
    primary: Optional[str] = None
    secondary: Optional[str] = None
    tertiary: Optional[str] = None

    def __init__(self, *args, **kwargs):
        if "tertiary" in kwargs and "secondary" not in kwargs and len(args) < 2:
            raise ValueError("Cannot have tertiary matchpoint without secondary.")

        values = list(args)
        for key in ["primary", "secondary", "tertiary"]:
            if key in kwargs:
                if len(values) < ["primary", "secondary", "tertiary"].index(key) + 1:
                    values.append(kwargs[key])

        while len(values) < 3:
            values.append(None)

        self.primary, self.secondary, self.tertiary = values[:3]

    def as_list(self) -> List[str]:
        return [i for i in (self.primary, self.secondary, self.tertiary) if i]

    def __composite_values__(self):
        return self.primary, self.secondary, self.tertiary

    def __eq__(self, other) -> bool:
        if not isinstance(other, Matchpoints):
            return NotImplemented
        return self.__composite_values__() == other.__composite_values__()

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


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

    def apply_template(self, template_data: Dict[str, Any]) -> None:
        for k, v in template_data.items():
            if v and k in self.__dict__.keys():
                setattr(self, k, v)


@dataclass(kw_only=True)
class Template:
    matchpoints: Matchpoints = field(default_factory=Matchpoints)
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
