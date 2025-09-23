from __future__ import annotations

import logging
from typing import Any

from bookops_marc import Bib

from overload_web.domain import models

logger = logging.getLogger(__name__)


class VendorIdentifier:
    def __init__(
        self,
        vendor_tags: dict[str, dict[str, dict[str, dict[str, str]]]],
        vendor_info: dict[str, Any],
    ) -> None:
        self.vendor_tags = vendor_tags
        self.vendor_info = vendor_info

    def _get_tag_from_bib(
        self, record: Bib, tags: dict[str, dict[str, str]]
    ) -> dict[str, str]:
        bib_dict: dict = {}
        for tag, data in tags.items():
            field = record.get(tag)
            if not field:
                continue
            else:
                bib_dict[tag] = {"code": data["code"], "value": field.get(data["code"])}
        return bib_dict

    def vendor_id(self, record: Bib) -> models.bibs.VendorInfo:
        for vendor, info in self.vendor_tags.items():
            tags: dict[str, dict[str, str]] = info.get("primary", {})
            tag_match = self._get_tag_from_bib(record=record, tags=tags)
            if tag_match and tag_match == tags:
                return models.bibs.VendorInfo(
                    name=vendor,
                    bib_fields=self.vendor_info[vendor]["bib_fields"],
                    matchpoints=self.vendor_info[vendor]["matchpoints"],
                )
            alt_tags = info.get("alternate", {})
            alt_match = self._get_tag_from_bib(record=record, tags=alt_tags)
            if alt_match and alt_match == alt_tags:
                return models.bibs.VendorInfo(
                    name=vendor,
                    bib_fields=self.vendor_info[vendor]["bib_fields"],
                    matchpoints=self.vendor_info[vendor]["matchpoints"],
                )
        return models.bibs.VendorInfo(
            name="UNKNOWN",
            bib_fields=self.vendor_info["UNKNOWN"]["bib_fields"],
            matchpoints=self.vendor_info["UNKNOWN"]["matchpoints"],
        )
