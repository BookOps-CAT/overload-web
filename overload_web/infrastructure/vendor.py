"""Parsers to identify vendor information within MARC records"""

from __future__ import annotations

import logging
from typing import Any

from bookops_marc import Bib

from overload_web.domain import models

logger = logging.getLogger(__name__)


class VendorIdentifier:
    """Parses MARC records to identify the records' vendors based on a set of rules."""

    def __init__(
        self,
        vendor_tags: dict[str, dict[str, dict[str, dict[str, str]]]],
        vendor_info: dict[str, Any],
    ) -> None:
        """
        Initialize `VendorIdentifier` using a specific set of marc mapping rules.

        Args:
            vendor_tags:
                A dictionary a list of vendors and tags that are present in their
                records.
            vendor_info:
                A dictionary containing information about matchpoints to use and fields
                to add to records for vendors.
        """
        self.vendor_tags = vendor_tags
        self.vendor_info = vendor_info

    def _get_tag_from_bib(
        self, record: Bib, tags: dict[str, dict[str, str]]
    ) -> dict[str, dict[str, str]]:
        """
        Get the MARC tag, subfield code, and value from a record based on a dictionary
        containing tags and subfield codes that would be present in a vendor's records

        Args:
            record: A bookops_marc.Bib object
            tags: A dictionary containing MARC tags, subfield codes, and subfield values

        Returns:
            A dictionary containing the values present in the MARC fields/subfields.

        """
        bib_dict: dict = {}
        for tag, data in tags.items():
            field = record.get(tag)
            if not field:
                continue
            else:
                bib_dict[tag] = {"code": data["code"], "value": field.get(data["code"])}
        return bib_dict

    def identify_vendor(self, record: Bib) -> models.bibs.VendorInfo:
        """Identify the vendor to whom a `bookops_marc.Bib` record belongs."""
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
