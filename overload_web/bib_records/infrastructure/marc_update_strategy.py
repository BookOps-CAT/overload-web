"""Parsers for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import json
import logging
from typing import Any

from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.bib_records.domain import bibs, marc_protocols
from overload_web.errors import OverloadError

logger = logging.getLogger(__name__)


class MarcUpdaterFactory:
    def make(self, record_type: str) -> marc_protocols.BibUpdateStrategy:
        with open("overload_web/vendor_specs.json", "r", encoding="utf-8") as fh:
            constants = json.load(fh)
        rules = constants["updater_rules"]
        if record_type == "acq":
            return AcquisitionsUpdateStrategy(rules=rules)
        elif record_type == "cat":
            return CatalogingUpdateStrategy(rules=rules)
        else:
            return SelectionUpdateStrategy(rules=rules)


class BookopsMarcUpdater:
    """Update MARC records based on attributes of domain objects."""

    def __init__(self, rules: dict[str, dict[str, str]]) -> None:
        """
        Initialize a `BookopsMarcUpdater` using a specific set of marc mapping rules.

        This class is a concrete implementation of the `MarcUpdater` protocol.

        Args:
            rules:
                A dictionary containing set of rules to use when mapping `Order`
                objects to MARC records. These rules map attributes of an `Order` to
                MARC fields and subfields.
        """
        self.rules = rules

    def update_bib_data(self, record: bibs.DomainBib) -> bibs.DomainBib:
        """Update the bib_id and add MARC fields to a `bibs.DomainBib` object."""
        bib_rec = Bib(record.binary_data, library=str(record.library))  # type: ignore
        if record.bib_id:
            bib_rec.remove_fields("907")
            bib_id = f".b{str(record.bib_id).strip('.b')}"
            bib_rec.add_ordered_field(
                Field(
                    tag="907",
                    indicators=Indicators(" ", " "),
                    subfields=[Subfield(code="a", value=bib_id)],
                )
            )
        for field in getattr(record.vendor_info, "bib_fields", []):
            bib_rec.add_ordered_field(
                Field(
                    tag=field["tag"],
                    indicators=Indicators(field["ind1"], field["ind2"]),
                    subfields=[
                        Subfield(code=field["subfield_code"], value=field["value"])
                    ],
                )
            )
        record.binary_data = bib_rec.as_marc()
        return record

    def update_order(self, record: bibs.DomainBib) -> bibs.DomainBib:
        """Update the MARC order fields within a `bibs.DomainBib` object."""
        bib_rec = Bib(record.binary_data, library=str(record.library))  # type: ignore
        for order in record.orders:
            order_data = order.map_to_marc(rules=self.rules)
            for tag in order_data.keys():
                subfields = []
                for k, v in order_data[tag].items():
                    if v is None:
                        continue
                    elif isinstance(v, list):
                        subfields.extend([Subfield(code=k, value=str(i)) for i in v])
                    else:
                        subfields.append(Subfield(code=k, value=str(v)))
                bib_rec.add_field(
                    Field(tag=tag, indicators=Indicators(" ", " "), subfields=subfields)
                )
        record.binary_data = bib_rec.as_marc()
        return record

    def update_acquisitions_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        """Update a MARC record based on its type and template data."""
        record.apply_order_template(template_data=template_data)
        record = self.update_order(record=record)
        return record

    def update_cataloging_record(self, record: bibs.DomainBib) -> bibs.DomainBib:
        """Update a MARC record based on its type and template data."""
        return self.update_bib_data(record=record)

    def update_selection_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        """Update a MARC record based on its type and template data."""
        record.apply_order_template(template_data=template_data)
        record = self.update_order(record=record)
        record = self.update_bib_data(record=record)
        return record


class AcquisitionsUpdateStrategy(BookopsMarcUpdater):
    def update_bib(
        self, records: list[bibs.DomainBib], template_data: dict[str, Any]
    ) -> list[bibs.DomainBib]:
        """
        Update bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.
            template_data:
                A dictionary containing template data to be used in updating records.

        Returns:
            A list of updated records as `bibs.DomainBib` objects
        """
        out = []
        for record in records:
            if not template_data:
                raise OverloadError(
                    "Order template required for acquisition or selection workflow."
                )
            rec = self.update_acquisitions_record(
                record=record, template_data=template_data
            )
            out.append(rec)
        return out


class CatalogingUpdateStrategy(BookopsMarcUpdater):
    def update_bib(
        self, records: list[bibs.DomainBib], *args, **kwargs
    ) -> list[bibs.DomainBib]:
        """
        Update bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.

        Returns:
            A list of updated records as `bibs.DomainBib` objects
        """
        out = []
        for record in records:
            if not record.vendor_info:
                raise OverloadError("Vendor index required for cataloging workflow.")
            rec = self.update_cataloging_record(record=record)
            out.append(rec)
        return out


class SelectionUpdateStrategy(BookopsMarcUpdater):
    def update_bib(
        self, records: list[bibs.DomainBib], template_data: dict[str, Any]
    ) -> list[bibs.DomainBib]:
        """
        Update bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.
            template_data:
                A dictionary containing template data to be used in updating records.

        Returns:
            A list of updated records as `bibs.DomainBib` objects
        """
        out = []
        for record in records:
            if not template_data:
                raise OverloadError(
                    "Order template required for acquisition or selection workflow."
                )
            rec = self.update_selection_record(
                record=record, template_data=template_data
            )
            out.append(rec)
        return out
