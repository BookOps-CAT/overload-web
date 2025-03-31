from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass
from typing import List, Optional, Union


def apply_template(bib: OrderBib, template: Template) -> OrderBib:
    for order in bib.orders:
        template_dict = asdict(template)
        for k, v in template_dict.items():
            if v and "matchpoint" not in k:
                setattr(order, k, v)
    return bib


@dataclass
class OrderBib:
    library: str
    orders: List[Order]
    bib_id: Optional[str] = None
    isbn: Optional[str] = None
    oclc_number: Optional[Union[str, List[str]]] = None
    upc: Optional[str] = None

    def attach(self, bib_ids: List[str]) -> None:
        if bib_ids:
            self.bib_id = bib_ids[0]
            self.all_bib_ids = bib_ids
        else:
            self.all_bib_ids = []


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


@dataclass(kw_only=True)
class Template:
    audience: Optional[str] = None
    blanket_po: Optional[str] = None
    copies: Optional[Union[str, int]] = None
    country: Optional[str] = None
    create_date: Optional[Union[datetime.datetime, datetime.date, str]] = None
    format: Optional[str] = None
    fund: Optional[str] = None
    internal_note: Optional[str] = None
    lang: Optional[str] = None
    order_type: Optional[str] = None
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


@dataclass(kw_only=True)
class PersistentTemplate(Template):
    id: Union[int, str]
    name: str
    agent: str
