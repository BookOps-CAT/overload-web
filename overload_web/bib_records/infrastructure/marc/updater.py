"""Parsers for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import logging
from typing import Any

from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.bib_records.domain import bibs

logger = logging.getLogger(__name__)


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
        record = self.update_bib_data(record=record)
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
