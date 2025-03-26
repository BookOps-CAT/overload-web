from __future__ import annotations

import datetime
from typing import Annotated, List, Optional, Union

from bookops_marc import Bib, SierraBibReader
from fastapi import Form, UploadFile
from pydantic import BaseModel, ConfigDict

from overload_web.adapters import marc_adapters
from overload_web.domain import model


class OrderModel(BaseModel, model.Order):
    model_config = ConfigDict(from_attributes=True)


class OrderBibModel(BaseModel, model.OrderBib):
    model_config = ConfigDict(from_attributes=True)


class TemplateModel(BaseModel, model.Template):
    model_config = ConfigDict(from_attributes=True)


class FormDataModel:
    model_config = ConfigDict(from_attributes=True)

    library: Annotated[str, Form()]
    create_date: Annotated[Optional[Union[datetime.datetime, str]], Form()] = None
    price: Annotated[Optional[Union[str, int]], Form()] = None
    fund: Annotated[Optional[str], Form()] = None
    copies: Annotated[Optional[Union[str, int]], Form()] = None
    lang: Annotated[Optional[str], Form()] = None
    country: Annotated[Optional[str], Form()] = None
    vendor_code: Annotated[Optional[str], Form()] = None
    format: Annotated[Optional[str], Form()] = None
    selector: Annotated[Optional[str], Form()] = None
    selector_note: Annotated[Optional[str], Form()] = None
    source: Annotated[Optional[str], Form()] = None
    order_type: Annotated[Optional[str], Form()] = None
    status: Annotated[Optional[str], Form()] = None
    internal_note: Annotated[Optional[str], Form()] = None
    var_field_isbn: Annotated[Optional[str], Form()] = None
    vendor_notes: Annotated[Optional[str], Form()] = None
    vendor_title_no: Annotated[Optional[str], Form()] = None
    blanket_po: Annotated[Optional[str], Form()] = None
    primary_matchpoint: Annotated[Optional[str], Form()] = None
    secondary_matchpoint: Annotated[Optional[str], Form()] = None
    tertiary_matchpoint: Annotated[Optional[str], Form()] = None
    destination: Annotated[Optional[str], Form()] = None


def order_mapper(record: Bib) -> List[model.Order]:
    return [
        OrderModel(
            audience=order.audience,
            blanket_po=order.blanket_po,
            copies=order.copies,
            country=order.country,
            create_date=order.created,
            format=order.form,
            fund=order.fund,
            internal_note=order.internal_note,
            lang=order.lang,
            locations=order.locs,
            order_type=order.order_type,
            price=order.price,
            selector=order.selector,
            selector_note=order.selector_note,
            source=order.source,
            status=order.status,
            var_field_isbn=order.var_field_isbn,
            vendor_code=order.vendor_code,
            vendor_notes=order.venNotes,
            vendor_title_no=order.vendor_title_no,
        )
        for order in marc_adapters.OverloadOrder.orders_from_bib(record)
    ]


def read_marc_file(marc_file: UploadFile, library: str) -> List[OrderBibModel]:
    record_list = []
    reader = SierraBibReader(marc_file.file, library=library, hide_utf8_warnings=True)
    for record in reader:
        overload_orders = marc_adapters.OverloadOrder.orders_from_bib(record)
        record_list.append(
            OrderBibModel(
                orders=order_mapper(record),
                bib_id=record.sierra_bib_id,
                isbn=record.isbn,
                oclc_number=list(record.oclc_nos.values()),
                upc=record.upc_number,
                library=library,
            )
        )
    return record_list
