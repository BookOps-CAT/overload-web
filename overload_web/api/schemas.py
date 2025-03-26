from __future__ import annotations

import datetime
import json
from typing import Annotated, Optional, Union

from fastapi import Form, UploadFile
from pydantic import BaseModel, ConfigDict

from overload_web.domain import model


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
) -> TemplateModel:
    return TemplateModel(
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
