import datetime
from typing import List, Optional, Union
from pydantic import BaseModel


class OrderModel(BaseModel):
    library: str
    create_date: Union[datetime.datetime, str]
    locations: List[str]
    shelves: List[str]
    price: Union[str, int]
    fund: str
    copies: Union[str, int]
    lang: str
    country: str
    vendor_code: str
    format: str
    selector: str
    audience: List[str]
    source: str
    order_type: str
    status: str
    internal_note: Optional[List[str]]
    var_field_isbn: Optional[List[str]]
    vendor_notes: Optional[str]
    vendor_title_no: Optional[str]
    blanket_po: Optional[str]
    bib_id: Optional[Union[str, int]]
    upc: Optional[Union[str, int]]
    isbn: Optional[Union[str, int]]
    oclc_number: Optional[Union[str, int]]


class OrderTemplateModel(BaseModel):
    create_date: Optional[Union[datetime.datetime, str]] = None
    locations: Optional[List[str]] = None
    shelves: Optional[List[str]] = None
    price: Optional[Union[str, int]] = None
    fund: Optional[str] = None
    copies: Optional[Union[str, int]] = None
    lang: Optional[str] = None
    country: Optional[str] = None
    vendor_code: Optional[str] = None
    format: Optional[str] = None
    selector: Optional[str] = None
    audience: Optional[List[str]] = None
    source: Optional[str] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    internal_note: Optional[List[str]] = None
    isbn: Optional[List[str]] = None
    vendor_notes: Optional[str] = None
    vendor_title_no: Optional[str] = None
    blanket_po: Optional[str] = None
    primary_matchpoint: Optional[str] = None
    secondary_matchpoint: Optional[str] = None
    tertiary_matchpoint: Optional[str] = None
