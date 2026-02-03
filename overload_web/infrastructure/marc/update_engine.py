"""Record updaters for MARC records using bookops_marc and pymarc."""

from __future__ import annotations

import logging
from typing import Any

from bookops_marc import Bib

from overload_web.domain.models import bibs
from overload_web.infrastructure.marc import update_steps

logger = logging.getLogger(__name__)


class BibUpdateEngine:
    def __init__(
        self,
        library: str,
        rules: dict[str, Any],
        record_type: str,
        collection: str | None,
    ) -> None:
        self.record_type = record_type
        self.library = library
        self.order_mapping = rules["update_order_mapping"]
        self.default_loc = rules["default_locations"][library].get(collection)
        self.bib_id_tag = rules["bib_id_tag"][library]

    def create_bib(self, record: bibs.DomainBib) -> Bib:
        return Bib(record.binary_data, library=record.library)  # type: ignore

    def update(self, record: bibs.DomainBib, **kwargs: Any) -> bibs.DomainBib:
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
        bib = self.create_bib(record=record)
        match self.record_type:
            case "acq":
                update_steps.MarcFields._apply_order_template(
                    bib=record, template_data=kwargs["template_data"]
                )
                update_steps.MarcFields._update_order_fields(
                    bib_rec=bib,
                    orders=record.orders,
                    mapping=self.order_mapping,
                )
            case "cat":
                update_steps.MarcFields._add_vendor_fields(
                    bib_rec=bib,
                    bib_fields=getattr(record.vendor_info, "bib_fields", []),
                )
            case _:  # sel
                update_steps.MarcFields._apply_order_template(
                    bib=record, template_data=kwargs["template_data"]
                )
                update_steps.MarcFields._update_order_fields(
                    bib_rec=bib,
                    orders=record.orders,
                    mapping=self.order_mapping,
                )
                update_steps.MarcFields._add_command_tag(
                    bib_rec=bib, template_data=kwargs["template_data"]
                )
                update_steps.MarcFields._set_default_location(
                    bib_rec=bib, default_loc=self.default_loc
                )
        match self.library:
            case "nypl":
                update_steps.MarcFields._add_bib_id(
                    bib_rec=bib, bib_id=record.bib_id, tag=self.bib_id_tag
                )
                update_steps.MarcFields._update_leader(bib_rec=bib)
                update_steps.MarcFields._update_910_field(bib_rec=bib)
                update_steps.MarcFields._update_bt_series_call_no(
                    bib_rec=bib,
                    collection=record.collection,
                    vendor=record.vendor,
                    record_type=record.record_type,
                )
            case _:  # bpl
                update_steps.MarcFields._add_bib_id(
                    bib_rec=bib, bib_id=record.bib_id, tag=self.bib_id_tag
                )
                update_steps.MarcFields._update_leader(bib_rec=bib)
        record.binary_data = bib.as_marc()
        return record
