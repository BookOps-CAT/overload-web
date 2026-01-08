"""Domain service for updating bib records"""

from __future__ import annotations

import logging
from collections import Counter
from itertools import chain
from typing import Any, Protocol, TypeVar, runtime_checkable

from overload_web.bib_records.domain_models import bibs, sierra_responses

logger = logging.getLogger(__name__)

T = TypeVar("T", contravariant=True)  # variable for contravariant `Bib` type


@runtime_checkable
class MarcUpdateHandler(Protocol[T]):
    full_record_pipelines: dict[str, Any]
    order_pipelines: dict[str, Any]
    library_pipelines: dict[str, Any]

    def create_order_marc_ctx(
        self,
        record: bibs.DomainBib,
        rules: dict[str, Any],
        template_data: dict[str, Any],
    ) -> Any: ...  # pragma: no branch

    def create_library_ctx(
        self, bib_id: str | None, bib_rec: T, vendor: str | None
    ) -> Any: ...  # pragma: no branch

    def create_full_marc_ctx(
        self, record: bibs.DomainBib
    ) -> Any: ...  # pragma: no branch


class OrderLevelBibUpdater:
    def __init__(
        self, rules: dict[str, Any], update_handler: MarcUpdateHandler
    ) -> None:
        self.rules = rules
        self.update_handler = update_handler

    def _update_order_record(
        self, record: bibs.DomainBib, template_data: dict[str, Any]
    ) -> bibs.DomainBib:
        ctx = self.update_handler.create_order_marc_ctx(
            record=record, template_data=template_data, rules=self.rules
        )
        pipeline = self.update_handler.order_pipelines[record.record_type]
        for step in pipeline:
            step.apply(ctx)
        library_ctx = self.update_handler.create_library_ctx(
            bib_rec=ctx.bib_rec,
            bib_id=record.bib_id,
            vendor=template_data.get("vendor"),
        )
        policies = self.update_handler.library_pipelines[record.library]
        for policy in policies:
            policy.apply(library_ctx)

        record.binary_data = ctx.bib_rec.as_marc()
        return record

    def update(
        self, records: list[bibs.DomainBib], template_data: dict[str, Any]
    ) -> list[bibs.DomainBib]:
        """
        Update order-level bibliographic records.

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
            rec = self._update_order_record(record=record, template_data=template_data)
            out.append(rec)
        return out


class FullLevelBibUpdater:
    def __init__(self, update_handler: MarcUpdateHandler) -> None:
        self.update_handler = update_handler

    def _update_full_record(self, record: bibs.DomainBib) -> bibs.DomainBib:
        ctx = self.update_handler.create_full_marc_ctx(record=record)
        pipeline = self.update_handler.full_record_pipelines[record.record_type]
        for step in pipeline:
            step.apply(ctx)
        library_ctx = self.update_handler.create_library_ctx(
            bib_rec=ctx.bib_rec, bib_id=record.bib_id, vendor=record.vendor
        )
        policies = self.update_handler.library_pipelines[record.library]
        for policy in policies:
            policy.apply(library_ctx)
        record.binary_data = ctx.bib_rec.as_marc()
        return record

    def _review_record(
        self, record: bibs.DomainBib, all_dupes: list[bibs.DomainBib]
    ) -> bibs.DomainBib:
        base_rec_ctx = self.update_handler.create_full_marc_ctx(record=all_dupes[0])
        if record.library == "nypl":
            tag = "949"
            ind2 = "1"
        else:
            tag = "960"
            ind2 = " "
        all_items = []
        for dupe in all_dupes[1:]:
            ctx = self.update_handler.create_full_marc_ctx(record=dupe)
            all_items.extend(ctx.bib_rec.get_fields(tag))
        for item in all_items:
            if item.indicator1 == " " and item.indicator2 == ind2:
                base_rec_ctx.bib_rec.add_ordered_field(item)
        record.binary_data = base_rec_ctx.bib_rec.as_marc()
        return record

    def update(self, records: list[bibs.DomainBib]) -> list[bibs.DomainBib]:
        """
        Update order-level bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.

        Returns:
            A list of updated records as `bibs.DomainBib` objects
        """
        out = []
        for record in records:
            rec = self._update_full_record(record=record)
            out.append(rec)
        return out

    def dedupe(
        self,
        records: list[bibs.DomainBib],
        reports: list[sierra_responses.MatchResolution],
    ) -> dict[str, list[bibs.DomainBib]]:
        merge_recs: list[bibs.DomainBib] = []
        new_recs: list[bibs.DomainBib] = []
        deduped_recs: list[bibs.DomainBib] = []
        for analysis, record in zip(reports, records):
            if analysis == sierra_responses.CatalogAction.ATTACH:
                merge_recs.append(record)
            else:
                new_recs.append(record)
        if not new_recs:
            return {"DUP": merge_recs, "NEW": new_recs, "DEDUPED": deduped_recs}
        logger.debug("Deduping new records")
        new_record_counter = Counter([i.control_number for i in new_recs])
        dupe_recs = [i for i, count in new_record_counter.items() if count > 1]
        if not dupe_recs:
            logger.debug("No duplicates found in file.")
            return {"DUP": merge_recs, "NEW": new_recs, "DEDUPED": deduped_recs}
        logger.debug("Discovered duplicate records in processed file")

        processed_dupes = []
        for record in new_recs:
            if record.control_number not in dupe_recs:
                deduped_recs.append(record)
            if record.control_number in processed_dupes:
                continue
            all_dupes = [
                i for i in new_recs if i.control_number == record.control_number
            ]
            merged_rec = self._review_record(record=record, all_dupes=all_dupes)
            processed_dupes.append(merged_rec.control_number)
            deduped_recs.append(merged_rec)
        return {"DUP": merge_recs, "NEW": new_recs, "DEDUPED": deduped_recs}

    def validate(
        self, record_batches: dict[str, list[bibs.DomainBib]], barcodes: list[str]
    ) -> None:
        valid = True
        barcodes_from_batches = []
        missing_barcodes = set()
        records = chain.from_iterable([v for k, v in record_batches.items()])
        for record in records:
            ctx = self.update_handler.create_full_marc_ctx(record=record)
            if record.library == "nypl":
                tag = "949"
                ind2 = "1"
            else:
                tag = "960"
                ind2 = " "
            for item in ctx.bib_rec.get_fields(tag):
                if item.indicator1 == " " and item.indicator2 == ind2:
                    barcodes_from_batches.extend(item.get_subfields("i"))
        for barcode in barcodes:
            if barcode not in barcodes_from_batches:
                valid = False
                missing_barcodes.add(barcode)
        valid = sorted(barcodes) == sorted(barcodes_from_batches)
        logger.debug(
            f"Integrity validation: {valid}, missing_barcodes: {missing_barcodes}"
        )
        if not valid:
            logger.error(f"Barcodes integrity error: {missing_barcodes}")
