"""Record updaters for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import logging
from typing import Any

from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.domain.models import bibs
from overload_web.domain.rules import vendor_rules

logger = logging.getLogger(__name__)


class BibUpdateEngine:
    def __init__(
        self,
        library: str,
        order_mapping: dict[str, Any],
        default_loc: str,
        bib_id_tag: str,
        record_type: str,
    ) -> None:
        self.library = library
        self.order_mapping = order_mapping
        self.default_loc = default_loc
        self.bib_id_tag = bib_id_tag
        self.record_type = record_type

    def _get_call_no_field(self, bib: Bib) -> str | None:
        if "091" in bib:
            return bib.get_fields("091")[0].value()
        return None

    def _get_command_tag_field(self, bib: Bib) -> Field | None:
        for field in bib.get_fields("949", []):
            if field.indicators == Indicators(" ", " ") and field.get(
                "a", ""
            ).startswith("*"):
                return field
        return None

    def create_bib(self, record: bibs.DomainBib) -> Bib:
        return Bib(record.binary_data, library=record.library)  # type: ignore

    def apply_updates(
        self, record: bibs.DomainBib, updates: list[Any], bib: Bib
    ) -> None:
        """
        Update a bibliographic record.

        Args:
            record:
                A parsed bibliographic record
            template_data:
                A dictionary containing template data to be used in updating records.
                This kwarg is only used for order-level records.

        Returns:
            An updated records as a `DomainBib` object
        """
        for update in updates:
            if update.delete:
                bib.remove_fields(update.tag)
            if update.original:
                bib.remove_field(update.original)
            bib.add_ordered_field(
                Field(
                    tag=update.tag,
                    indicators=Indicators(update.ind1, update.ind1),
                    subfields=[
                        Subfield(code=i["code"], value=i["value"])
                        for i in update.subfields
                    ],
                )
            )
        bib.leader = vendor_rules.FieldRules.update_leader(bib.leader)
        record.binary_data = bib.as_marc()
