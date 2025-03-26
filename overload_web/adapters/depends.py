from __future__ import annotations

import datetime
import io
from typing import Annotated, Generator, Optional, Union

from bookops_marc import SierraBibReader
from fastapi import Form

from overload_web.adapters import marc_adapters
from overload_web.api import schemas


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
        schemas.TemplateModel(
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


def read_marc_file(
    marc_file: io.BytesIO, library: str
) -> Generator[schemas.OrderBibModel, None, None]:
    reader = SierraBibReader(marc_file, library=library, hide_utf8_warnings=True)
    for record in reader:
        record = marc_adapters.OverloadBib.bib2overload_bib(record)
        yield schemas.OrderBibModel.from_overload_bib(record)
