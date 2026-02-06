"""Domain service for updating bib records"""

from __future__ import annotations

import logging
from collections import Counter
from itertools import chain
from typing import Any, Protocol, TypeVar

from overload_web.application.ports import marc
from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)
C = TypeVar("C")


class ReportHandler(Protocol[C]):
    creds: C

    def configure_sheet(self) -> C: ...  # pragma: no branch

    def create_duplicate_report(
        self, data: dict[str, Any]
    ) -> list[list[Any]]: ...  # pragma: no branch

    def create_call_number_report(
        self, data: dict[str, Any]
    ) -> list[list[Any]]: ...  # pragma: no branch

    def write_report_to_sheet(
        self, data: list[list[Any]]
    ) -> None: ...  # pragma: no branch


class BibReviewer:
    def __init__(self, port: marc.MarcEnginePort) -> None:
        self.port = port

    def _merge_record(
        self, record: bibs.DomainBib, all_dupes: list[bibs.DomainBib]
    ) -> bibs.DomainBib:
        base_rec = self.port.create_bib_from_domain(record=all_dupes[0])
        if record.library == "bpl" and base_rec.overdrive_number is None:
            tag = "960"
            ind2 = " "
        else:
            tag = "949"
            ind2 = "1"
        all_items = []
        for dupe in all_dupes[1:]:
            bib = self.port.create_bib_from_domain(record=dupe)
            all_items.extend(bib.get_fields(tag))
        for item in all_items:
            if item.indicator1 == " " and item.indicator2 == ind2:
                base_rec.add_ordered_field(item)
        record.binary_data = base_rec.as_marc()
        return record

    def dedupe(
        self,
        records: list[bibs.DomainBib],
        reports: list[bibs.MatchAnalysis],
    ) -> dict[str, list[bibs.DomainBib]]:
        merge_recs: list[bibs.DomainBib] = []
        new_recs: list[bibs.DomainBib] = []
        deduped_recs: list[bibs.DomainBib] = []
        for analysis, record in zip(reports, records):
            if analysis.action == bibs.CatalogAction.ATTACH:
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
        self,
        record_batches: dict[str, list[bibs.DomainBib]],
        barcodes: list[str] = [],
    ) -> None:
        valid = True
        barcodes_from_batches = list(
            chain.from_iterable(i.barcodes for j in record_batches.values() for i in j)
        )
        missing_barcodes = set()
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

    def dedupe_and_validate(
        self,
        records: list[bibs.DomainBib],
        reports: list[bibs.MatchAnalysis],
        barcodes: list[str],
    ) -> dict[str, list[bibs.DomainBib]]:
        """
        Review full-level bibliographic records before serializing records to MARC.

        Args:
            records:
                a list of bib records represented at `DomainBib` objects.
            reports:
                a list of bib records and their associated match analysis results
                as `MatchAnalysis` objects.
            barcodes:
                the list of all barcodes present in the file extracted from the
                records at the beginning of processing.
        Returns:
            a dictionary containing the `DomainBib` objects to be written and
            the file that they should be written to.
        """
        deduped_recs = self.dedupe(records=records, reports=reports)
        self.validate(record_batches=deduped_recs, barcodes=barcodes)
        return deduped_recs

    def review_processed_records(
        self,
        records: list[bibs.DomainBib],
        reports: list[bibs.MatchAnalysis],
        barcodes: list[str] = [],
    ) -> dict[str, list[bibs.DomainBib]]:
        """
        Review processed bibliographic records before serializing records to MARC.

        Args:
            records:
                a list of bib records represented at `DomainBib` objects.
            reports:
                a list of bib records and their associated match analysis results
                as `MatchAnalysis` objects.
            barcodes:
                an optional list of barcodes present in the file extracted from the
                records at the beginning of processing. used to deduplicate files
                of full MARC records
        Returns:
            a dictionary containing the `DomainBib` objects to be written and
            the file that they should be written to.
        """
        out = {}
        if all(i.record_type == "cat" for i in records):
            deduped_recs = self.dedupe(records=records, reports=reports)
            self.validate(record_batches=deduped_recs, barcodes=barcodes)
            out.apply_updates(deduped_recs)
            return deduped_recs
        return {"NEW": records}


class BibReporter:
    def __init__(self, handler: ReportHandler) -> None:
        self.handler = handler

    def report_on_files(self, data: dict[str, Any]) -> None:
        call_no_report = self.handler.create_call_number_report(data=data)
        if call_no_report:
            self.handler.write_report_to_sheet(data=call_no_report)
        dupe_report = self.handler.create_duplicate_report(data=data)
        if dupe_report:
            self.handler.write_report_to_sheet(data=dupe_report)
