"""Shared schemas to be used in multiple layers of application"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class _VendorFile:
    content: bytes
    file_name: str


@dataclass
class _Matchpoints:
    primary_matchpoint: str | None = None
    secondary_matchpoint: str | None = None
    tertiary_matchpoint: str | None = None


@dataclass
class _TemplateData:
    acquisition_type: str | None = None
    blanket_po: str | None = None
    claim_code: str | None = None
    country: str | None = None
    format: str | None = None
    internal_note: str | None = None
    lang: str | None = None
    material_form: str | None = None
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


@dataclass
class _TemplateBase(_TemplateData):
    agent: str | None = None
    name: str | None = None
    primary_matchpoint: str | None = None
    secondary_matchpoint: str | None = None
    tertiary_matchpoint: str | None = None
