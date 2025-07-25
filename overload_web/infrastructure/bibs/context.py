"""Defines context used for record processing."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from bookops_marc import Bib


@lru_cache
def load_vendor_rules() -> dict[str, dict[str, str | dict[str, str]]]:
    with open("overload_web/constants.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return constants["vendor_rules"]


class VendorIdentifier:
    def __init__(self, library: str, collection: str) -> None:
        self.library = library
        self.collection = collection
        self.vendor_rules: dict[str, Any] = load_vendor_rules().get(
            str(self.library), {}
        )

    def identify_vendor(self, bib: Bib) -> dict[str, Any]:
        vendor = "UNKNOWN"
        for vendor, info in self.vendor_rules.items():
            match_dict = info["vendor_tags"]
            bib_dict: dict = {}
            for field, data in match_dict.items():
                bib_field = bib.get(field)
                if not bib_field:
                    continue
                else:
                    bib_dict[field] = {
                        "code": data["code"],
                        "value": bib_field.get(data["code"]),
                    }
            if bib_dict and bib_dict == match_dict:
                return self.vendor_rules[vendor]
        return self.vendor_rules[vendor]
