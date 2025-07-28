from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Form
from pydantic import field_validator
from sqlmodel import Field, MetaData, SQLModel

logger = logging.getLogger(__name__)
metadata = MetaData()


class _TemplateBase(SQLModel):
    name: Annotated[str, Field(nullable=False, unique=True, index=True)]
    agent: Annotated[str, Field(nullable=False, index=True)]
    acquisition_type: Annotated[str | None, Field(default=None)]
    blanket_po: Annotated[str | None, Field(default=None)]
    claim_code: Annotated[str | None, Field(default=None)]
    country: Annotated[str | None, Field(default=None)]
    format: Annotated[str | None, Field(default=None)]
    internal_note: Annotated[str | None, Field(default=None)]
    lang: Annotated[str | None, Field(default=None)]
    material_form: Annotated[str | None, Field(default=None)]
    order_code_1: Annotated[str | None, Field(default=None)]
    order_code_2: Annotated[str | None, Field(default=None)]
    order_code_3: Annotated[str | None, Field(default=None)]
    order_code_4: Annotated[str | None, Field(default=None)]
    order_note: Annotated[str | None, Field(default=None)]
    order_type: Annotated[str | None, Field(default=None)]
    receive_action: Annotated[str | None, Field(default=None)]
    selector_note: Annotated[str | None, Field(default=None)]
    vendor_code: Annotated[str | None, Field(default=None)]
    vendor_notes: Annotated[str | None, Field(default=None)]
    vendor_title_no: Annotated[str | None, Field(default=None)]
    primary_matchpoint: Annotated[str, Field(nullable=False)]
    secondary_matchpoint: Annotated[str | None, Field(default=None)]
    tertiary_matchpoint: Annotated[str | None, Field(default=None)]


class Template(_TemplateBase, table=True):
    id: Annotated[int, Field(default=None, primary_key=True, index=True)]


class TemplatePublic(_TemplateBase):
    id: int


class TemplateCreate(_TemplateBase):
    ...

    @classmethod
    def from_form(
        cls,
        name: Annotated[str, Form()],
        agent: Annotated[str, Form()],
        acquisition_type: Annotated[str | None, Form(None)],
        blanket_po: Annotated[str | None, Form(None)],
        claim_code: Annotated[str | None, Form(None)],
        country: Annotated[str | None, Form(None)],
        format: Annotated[str | None, Form(None)],
        internal_note: Annotated[str | None, Form(None)],
        lang: Annotated[str | None, Form(None)],
        material_form: Annotated[str | None, Field(default=None)],
        order_code_1: Annotated[str | None, Form(None)],
        order_code_2: Annotated[str | None, Form(None)],
        order_code_3: Annotated[str | None, Form(None)],
        order_code_4: Annotated[str | None, Form(None)],
        order_note: Annotated[str | None, Form(None)],
        order_type: Annotated[str | None, Form(None)],
        receive_action: Annotated[str | None, Form(None)],
        selector_note: Annotated[str | None, Form(None)],
        vendor_code: Annotated[str | None, Form(None)],
        vendor_notes: Annotated[str | None, Form(None)],
        vendor_title_no: Annotated[str | None, Form(None)],
        primary_matchpoint: Annotated[str, Form()],
        secondary_matchpoint: Annotated[str | None, Form(None)],
        tertiary_matchpoint: Annotated[str | None, Form(None)],
    ) -> TemplateCreate:
        return TemplateCreate(
            name=name,
            agent=agent,
            acquisition_type=acquisition_type,
            blanket_po=blanket_po,
            claim_code=claim_code,
            country=country,
            format=format,
            internal_note=internal_note,
            lang=lang,
            material_form=material_form,
            order_code_1=order_code_1,
            order_code_2=order_code_2,
            order_code_3=order_code_3,
            order_code_4=order_code_4,
            order_note=order_note,
            order_type=order_type,
            receive_action=receive_action,
            selector_note=selector_note,
            vendor_code=vendor_code,
            vendor_notes=vendor_notes,
            vendor_title_no=vendor_title_no,
            primary_matchpoint=primary_matchpoint,
            secondary_matchpoint=secondary_matchpoint,
            tertiary_matchpoint=tertiary_matchpoint,
        )

    @field_validator("*", mode="before")
    @classmethod
    def parse_form_fields(cls, value: str) -> str | None:
        if value == "" or value.strip() == "":
            return None
        else:
            return value.strip()


class TemplateUpdate(SQLModel):
    name: str | None = None
    agent: str | None = None
    acquisition_type: str | None = None
    blanket_po: str | None = None
    claim_code: str | None = None
    country: str | None = None
    format: str | None = None
    internal_note: str | None = None
    lang: str | None = None
    material_form: str | None
    order_code_1: str | None = None
    order_code_2: str | None = None
    order_code_3: str | None = None
    order_code_4: str | None = None
    order_note: str | None = None
    order_type: str | None = None
    receive_action: str | None = None
    selector_note: str | None = None
    vendor_code: str | None = None
    vendor_notes: str | None = None
    vendor_title_no: str | None = None
    primary_matchpoint: str | None = None
    secondary_matchpoint: str | None = None
    tertiary_matchpoint: str | None = None
