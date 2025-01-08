from __future__ import annotations
import datetime
import json
from typing import Annotated, List, Literal, Optional, Union
from fastapi import Form, UploadFile
from pydantic import BaseModel


def get_template(
    create_date: Annotated[Optional[Union[datetime.datetime, str]], Form()],
    price: Annotated[Optional[Union[str, int]], Form()],
    fund: Annotated[Optional[str], Form()],
    copies: Annotated[Optional[Union[str, int]], Form()],
    lang: Annotated[Optional[str], Form()],
    country: Annotated[Optional[str], Form()],
    vendor_code: Annotated[Optional[str], Form()],
    format: Annotated[Optional[str], Form()],
    selector: Annotated[Optional[str], Form()],
    source: Annotated[Optional[str], Form()],
    order_type: Annotated[Optional[str], Form()],
    status: Annotated[Optional[str], Form()],
    internal_note: Annotated[Optional[str], Form()],
    var_field_isbn: Annotated[Optional[str], Form()],
    vendor_notes: Annotated[Optional[str], Form()],
    vendor_title_no: Annotated[Optional[str], Form()],
    blanket_po: Annotated[Optional[str], Form()],
    primary_matchpoint: Annotated[Optional[str], Form()],
    secondary_matchpoint: Annotated[Optional[str], Form()],
    tertiary_matchpoint: Annotated[Optional[str], Form()],
) -> OrderTemplateModel:
    return OrderTemplateModel(
        create_date=create_date,
        fund=fund,
        vendor_code=vendor_code,
        vendor_title_no=vendor_title_no,
        selector=selector,
        source=source,
        order_type=order_type,
        price=price,
        status=status,
        internal_note=internal_note,
        var_field_isbn=var_field_isbn,
        vendor_notes=vendor_notes,
        copies=copies,
        format=format,
        lang=lang,
        country=country,
        blanket_po=blanket_po,
        primary_matchpoint=primary_matchpoint,
        secondary_matchpoint=secondary_matchpoint,
        tertiary_matchpoint=tertiary_matchpoint,
    )


def get_order_file(
    order_file: UploadFile,
) -> OrderModel:
    order_data = order_file.file
    order = json.load(order_data)
    return OrderModel(**order)


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
    audience: str
    source: str
    order_type: str
    status: str
    internal_note: Optional[str]
    var_field_isbn: Optional[str]
    vendor_notes: Optional[str]
    vendor_title_no: Optional[str]
    blanket_po: Optional[str]
    bib_id: Optional[Union[str, int]]
    upc: Optional[Union[str, int]]
    isbn: Optional[Union[str, int]]
    oclc_number: Optional[Union[str, int]]


class OrderTemplateModel(BaseModel):
    create_date: Optional[Union[datetime.datetime, str]] = None
    price: Optional[Union[str, int]] = None
    fund: Optional[str] = None
    copies: Optional[Union[str, int]] = None
    lang: Optional[str] = None
    country: Optional[str] = None
    vendor_code: Optional[str] = None
    format: Optional[str] = None
    selector: Optional[str] = None
    audience: Optional[str] = None
    source: Optional[str] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    internal_note: Optional[str] = None
    var_field_isbn: Optional[str] = None
    vendor_notes: Optional[str] = None
    vendor_title_no: Optional[str] = None
    blanket_po: Optional[str] = None
    # primary_matchpoint: Optional[str] = None
    # secondary_matchpoint: Optional[str] = None
    # tertiary_matchpoint: Optional[str] = None
    primary_matchpoint: Optional[str] = None
    secondary_matchpoint: Optional[str] = None
    tertiary_matchpoint: Optional[str] = None
