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

    @classmethod
    def from_domain_model(cls, order: model.Order) -> OrderModel:
        return OrderModel(
            audience=order.audience,
            blanket_po=order.blanket_po,
            copies=order.copies,
            country=order.country,
            create_date=order.create_date,
            format=order.format,
            fund=order.fund,
            internal_note=order.internal_note,
            lang=order.lang,
            locations=order.locations,
            order_type=order.order_type,
            price=order.price,
            selector=order.selector,
            selector_note=order.selector_note,
            source=order.source,
            status=order.status,
            var_field_isbn=order.var_field_isbn,
            vendor_code=order.vendor_code,
            vendor_notes=order.vendor_notes,
            vendor_title_no=order.vendor_title_no,
        )


class OrderBibModel(BaseModel, model.OrderBib):
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain_model(cls, order_bib: model.OrderBib) -> OrderBibModel:
        return OrderBibModel(
            library=order_bib.library,
            orders=order_bib.orders,
            bib_id=order_bib.bib_id,
            isbn=order_bib.isbn,
            oclc_number=order_bib.oclc_number,
            upc=order_bib.upc,
        )


class TemplateModel(BaseModel, model.Template):
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain_model(cls, template: model.Template) -> TemplateModel:
        return TemplateModel(
            audience=template.audience,
            blanket_po=template.blanket_po,
            copies=template.copies,
            country=template.country,
            create_date=template.create_date,
            format=template.format,
            fund=template.fund,
            internal_note=template.internal_note,
            lang=template.lang,
            order_type=template.order_type,
            price=template.price,
            selector=template.selector,
            selector_note=template.selector_note,
            source=template.source,
            status=template.status,
            var_field_isbn=template.var_field_isbn,
            vendor_code=template.vendor_code,
            vendor_notes=template.vendor_notes,
            vendor_title_no=template.vendor_title_no,
            primary_matchpoint=template.primary_matchpoint,
            secondary_matchpoint=template.secondary_matchpoint,
            tertiary_matchpoint=template.tertiary_matchpoint,
        )


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


def get_form_data(
    library: Annotated[str, Form()],
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
    destination: Annotated[Optional[str], Form()] = None,
) -> tuple:
    return (
        library,
        destination,
        TemplateModel(
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
        ),
    )
