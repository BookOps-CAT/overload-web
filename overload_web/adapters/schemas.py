from __future__ import annotations

import datetime
from typing import Annotated, List, Optional, Union

from bookops_marc import Bib, SierraBibReader
from bookops_marc.models import Field
from bookops_marc.models import Order as BookopsMarcOrder
from fastapi import Form, UploadFile
from pydantic import BaseModel, ConfigDict

from overload_web.domain import model


class OrderModel(BaseModel, model.Order):
    model_config = ConfigDict(from_attributes=True)


class OrderBibModel(BaseModel, model.OrderBib):
    model_config = ConfigDict(from_attributes=True)


class OrderTemplateModel(BaseModel, model.OrderTemplate):
    model_config = ConfigDict(from_attributes=True)


class OverloadOrder(BookopsMarcOrder):
    def __init__(self, field: Field, following_field: Optional[Field] = None) -> None:
        super().__init__(field, following_field)

    def _get_subfield_from_following_field(self, code: str) -> Optional[str]:
        if self._following_field and self._following_field.tag == "961":
            subfield = self._following_field.get(code, None)
            return subfield
        else:
            return None

    @property
    def audience(self) -> Optional[str]:
        return self._field.get("f", None)

    @property
    def blanket_po(self) -> Optional[str]:
        return self._get_subfield_from_following_field("m")

    @property
    def country(self) -> Optional[str]:
        return self._field.get("x", None)

    @property
    def fund(self) -> Optional[str]:
        return self._field.get("u", None)

    @property
    def internal_note(self) -> Optional[str]:
        return self._get_subfield_from_following_field("d")

    @property
    def order_type(self) -> Optional[str]:
        return self._field.get("i", None)

    @property
    def price(self) -> Optional[str]:
        return self._field.get("s", None)

    @property
    def selector(self) -> Optional[str]:
        return self._field.get("c", None)

    @property
    def source(self) -> Optional[str]:
        return self._field.get("e", None)

    @property
    def status(self) -> Optional[str]:
        return self._field.get("m", None)

    @property
    def vendor_code(self) -> Optional[str]:
        return self._field.get("v", None)

    @property
    def var_field_isbn(self) -> Optional[str]:
        return self._get_subfield_from_following_field("l")

    @property
    def selector_note(self) -> Optional[str]:
        return self._get_subfield_from_following_field("f")

    @property
    def vendor_title_no(self) -> Optional[str]:
        return self._get_subfield_from_following_field("i")


def get_library(context: dict):
    try:
        return context["library"]
    except IndexError:
        return None


def get_template(
    create_date: Annotated[Optional[Union[datetime.datetime, str]], Form()] = None,
    price: Annotated[Optional[Union[str, int]], Form()] = None,
    fund: Annotated[Optional[str], Form()] = None,
    copies: Annotated[Optional[Union[str, int]], Form()] = None,
    lang: Annotated[Optional[str], Form()] = None,
    country: Annotated[Optional[str], Form()] = None,
    vendor_code: Annotated[Optional[str], Form()] = None,
    format: Annotated[Optional[str], Form()] = None,
    selector: Annotated[Optional[str], Form()] = None,
    selector_note: Annotated[Optional[str], Form()] = None,
    source: Annotated[Optional[str], Form()] = None,
    order_type: Annotated[Optional[str], Form()] = None,
    status: Annotated[Optional[str], Form()] = None,
    internal_note: Annotated[Optional[str], Form()] = None,
    var_field_isbn: Annotated[Optional[str], Form()] = None,
    vendor_notes: Annotated[Optional[str], Form()] = None,
    vendor_title_no: Annotated[Optional[str], Form()] = None,
    blanket_po: Annotated[Optional[str], Form()] = None,
    primary_matchpoint: Annotated[Optional[str], Form()] = None,
    secondary_matchpoint: Annotated[Optional[str], Form()] = None,
    tertiary_matchpoint: Annotated[Optional[str], Form()] = None,
) -> OrderTemplateModel:
    return OrderTemplateModel(
        create_date=create_date,
        fund=fund,
        vendor_code=vendor_code,
        vendor_title_no=vendor_title_no,
        selector=selector,
        selector_note=selector_note,
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


def order_mapper(record: Bib) -> List[model.Order]:
    orders: List[OverloadOrder] = []
    for field in record:
        if field.tag == "960":
            try:
                following_field = record.fields[record.pos]
            except IndexError:
                following_field = None
            orders.append(OverloadOrder(field, following_field))
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
        for order in orders
    ]


def read_marc_file(marc_file: UploadFile, library: str) -> List[OrderBibModel]:
    record_list = []
    reader = SierraBibReader(marc_file.file, library=library, hide_utf8_warnings=True)
    for record in reader:
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
