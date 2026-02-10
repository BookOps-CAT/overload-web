import logging
from typing import Any, BinaryIO

from overload_web.application.services import (
    marc_services,
    record_service,
    report_service,
)
from overload_web.domain.models import rules

logger = logging.getLogger(__name__)


class ProcessBatch:
    """Handles parsing, matching, and analysis of MARC records."""

    @staticmethod
    def execute_full_records_workflow(
        data: BinaryIO | bytes,
        file_name: str,
        handler: record_service.ProcessingHandler,
    ) -> tuple:
        bibs = marc_services.BibParser.parse_marc_data(data=data, engine=handler.engine)
        marc_services.BarcodeValidator.ensure_unique(bibs)
        barcodes = marc_services.BarcodeExtractor.extract_barcodes(bibs)
        for bib in bibs:
            matches = handler.match_service.match_full_record(bib)
            analysis = handler.analysis_service.analyze(record=bib, candidates=matches)
            bib.apply_match(analysis)
            marc_record = handler.engine.create_bib_from_domain(record=bib)
            updates = rules.VendorRules.fields_to_update(
                record=bib,
                context=handler.engine._config,
                call_no=handler.engine.get_value_of_field(tag="091", bib=marc_record),
                command_tag=handler.engine.get_command_tag_field(marc_record),
                template_data={},
            )
            handler.engine.update_fields(field_updates=updates, bib=marc_record)
            marc_record.leader = rules.FieldRules.update_leader(marc_record.leader)
            bib.binary_data = marc_record.as_marc()

        batches = marc_services.Deduplicator.deduplicate(
            records=bibs, engine=handler.engine
        )
        marc_services.BarcodeValidator.ensure_preserved(
            record_batches=batches, barcodes=barcodes
        )
        stats = report_service.ReportGenerator.processing_report(
            bibs, file_name=file_name
        )
        out = {k: marc_services.BibSerializer.write(v) for k, v in batches.items()}

        return out, stats

    @staticmethod
    def execute_order_records_workflow(
        data: BinaryIO | bytes,
        file_name: str,
        handler: record_service.ProcessingHandler,
        matchpoints: dict[str, str],
        template_data: dict[str, Any],
        vendor: str | None = None,
    ) -> tuple:
        bibs = marc_services.BibParser.parse_marc_data(
            data=data, engine=handler.engine, vendor=vendor
        )
        marc_services.BarcodeValidator.ensure_unique(bibs)
        for bib in bibs:
            matches = handler.match_service.match_order_record(
                bib, matchpoints=matchpoints
            )
            analysis = handler.analysis_service.analyze(record=bib, candidates=matches)
            bib.apply_match(analysis)
            bib.apply_order_template(template_data)
            marc_record = handler.engine.create_bib_from_domain(record=bib)
            updates = rules.VendorRules.fields_to_update(
                record=bib,
                context=handler.engine._config,
                call_no=handler.engine.get_value_of_field(tag="091", bib=marc_record),
                command_tag=handler.engine.get_command_tag_field(marc_record),
                template_data=template_data,
            )
            handler.engine.update_fields(field_updates=updates, bib=marc_record)
            marc_record.leader = rules.FieldRules.update_leader(marc_record.leader)
            bib.binary_data = marc_record.as_marc()

        stream = marc_services.BibSerializer.write(bibs)
        stats = report_service.ReportGenerator.processing_report(
            bibs, file_name=file_name
        )

        return stream, stats
