"""Domain service for updating bib records"""

from __future__ import annotations

import logging
from collections import Counter
from itertools import chain
from typing import Any, Protocol

from overload_web.bib_records.domain_models import bibs, matches

logger = logging.getLogger(__name__)


class UpdateStep(Protocol):
    def apply(self, ctx: Any) -> None: ...  # pragma: no branch


class MarcUpdateStrategy(Protocol):
    @property
    def pipeline(self) -> list[UpdateStep]: ...  # pragma: no branch
    def create_context(
        self, record: bibs.DomainBib, **kwargs: Any
    ) -> Any: ...  # pragma: no branch


class FullLevelBibReviewer:
    def __init__(self, context_factory: MarcUpdateStrategy) -> None:
        self.context_factory = context_factory

    def _merge_record(
        self, record: bibs.DomainBib, all_dupes: list[bibs.DomainBib]
    ) -> bibs.DomainBib:
        base_rec_ctx = self.context_factory.create_context(record=all_dupes[0])
        if record.library == "bpl" and base_rec_ctx.bib_rec.overdrive_number is None:
            tag = "960"
            ind2 = " "
        else:
            tag = "949"
            ind2 = "1"
        all_items = []
        for dupe in all_dupes[1:]:
            ctx = self.context_factory.create_context(record=dupe)
            all_items.extend(ctx.bib_rec.get_fields(tag))
        for item in all_items:
            if item.indicator1 == " " and item.indicator2 == ind2:
                base_rec_ctx.bib_rec.add_ordered_field(item)
        record.binary_data = base_rec_ctx.bib_rec.as_marc()
        return record

    def dedupe(
        self,
        records: list[bibs.DomainBib],
        reports: list[matches.MatchAnalysis],
    ) -> dict[str, list[bibs.DomainBib]]:
        merge_recs: list[bibs.DomainBib] = []
        new_recs: list[bibs.DomainBib] = []
        deduped_recs: list[bibs.DomainBib] = []
        for analysis, record in zip(reports, records):
            if analysis == matches.CatalogAction.ATTACH:
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
            merged_rec = self._merge_record(record=record, all_dupes=all_dupes)
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
            ctx = self.context_factory.create_context(record=record)
            if record.library == "bpl" and ctx.bib_rec.overdrive_number is None:
                tag = "960"
                ind2 = " "
            else:
                tag = "949"
                ind2 = "1"
            for item in ctx.bib_rec.get_fields(tag):
                if item.indicator1 == " " and item.indicator2 == ind2:
                    barcodes_from_batches.extend(item.get_subfields("i"))
        for barcode in barcodes:
            if barcode not in barcodes_from_batches:
                valid = False
                missing_barcodes.add(barcode)
        valid = sorted(barcodes) == sorted(barcodes_from_batches)
        logger.debug(
            f"Integrity validation: {valid}, missing_barcodes: {list(missing_barcodes)}"
        )
        if not valid:
            logger.error(f"Barcodes integrity error: {list(missing_barcodes)}")

    # def review_records(self) -> dict[str, list[bibs.DomainBib]]:

    def review_records(self) -> None:
        """Review full-level bibliographic records before finalizing updates."""
        pass  # Implementation would go here
