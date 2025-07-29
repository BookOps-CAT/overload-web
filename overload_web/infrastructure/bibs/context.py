"""Defines context used for record processing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from bookops_marc import Bib


class VendorIdentifier:
    def __init__(self, vendor_rules: dict[str, Any]) -> None:
        self.vendor_rules = vendor_rules

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
