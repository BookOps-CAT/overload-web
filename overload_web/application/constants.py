"""Constant values used in the application layer of overload_web"""

from __future__ import annotations

from typing import Any

MARC_MAPPING: dict[str, Any] = {
    "907": {"a", "bib_id"},
    "960": {
        "c": "order_code_1",
        "d": "order_code_2",
        "e": "order_code_3",
        "f": "order_code_4",
        "g": "format",
        "i": "order_type",
        "m": "status",
        "o": "copies",
        "q": "create_date",
        "s": "price",
        "t": "locations",
        "u": "fund",
        "v": "vendor_code",
        "w": "lang",
        "x": "country",
        "z": "order_id",
    },
    "961": {
        "d": "internal_note",
        "f": "selector_note",
        "h": "vendor_notes",
        "i": "vendor_title_no",
        "l": "var_field_isbn",
        "m": "blanket_po",
    },
}
