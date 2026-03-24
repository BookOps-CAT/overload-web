import logging
from typing import Any

from overload_web.application.services import marc_services, record_service
from overload_web.domain.models import bibs

logger = logging.getLogger(__name__)


class CombineMarcFiles:
    """Combine multiple MARC files into one for processing CAT records."""

    @staticmethod
    def execute(data: list[bytes], handler: record_service.ProcessingHandler) -> bytes:
        return marc_services.MarcFileMerger.combine_marc_files(
            data=data, engine=handler.engine
        )


class ProcessFullRecords:
    """Handles parsing, matching, and analysis of full MARC records."""

    @staticmethod
    def execute(
        data: bytes, handler: record_service.ProcessingHandler
    ) -> bibs.ProcessedMarcFile:
        """
        Process a file of full MARC records.

        This service parses full MARC records, matches them against Sierra, analyzes
        all bibs that were returned as matches, updates the records with required
        fields, and outputs the updated records and the match analysis.

        Args:
            data: binary MARC data as a `bytes` object.
            file_name: the name of the file being processed.
            handler: a `ProcessingHandler` object used by the command.
        Returns:
            A `ProcessedFullMarcFile` object containing the processed records,
            the file name and the processing statistics
        """
        records = marc_services.BibParser.parse_marc_data(
            data=data, engine=handler.engine
        )
        marc_services.BarcodeValidator.ensure_unique(records)
        barcodes = marc_services.BarcodeExtractor.extract_barcodes(records)
        for bib in records:
            matches = handler.match_service.match_full_record(bib)
            analysis = bib.analyze_matches(candidates=matches)
            bib.apply_match(analysis)
            marc_services.BibUpdater.update_record(bib, engine=handler.engine)

        missing_barcodes = marc_services.BarcodeValidator.ensure_preserved(
            records=records, barcodes=barcodes
        )
        out = bibs.ProcessedMarcFile(records=records, missing_barcodes=missing_barcodes)
        return out


class ProcessOrderRecords:
    """Handles parsing, matching, and analysis of order-level MARC records."""

    @staticmethod
    def execute(
        data: bytes,
        file_name: str,
        handler: record_service.ProcessingHandler,
        matchpoints: dict[str, str],
        template_data: dict[str, Any],
    ) -> bibs.ProcessedMarcFile:
        """
        Process a file of order-level MARC records.

        This service parses order-level MARC records, matches them against Sierra,
        analyzes all bibs that were returned as matches, updates the records with
        required fields, and outputs the updated records and the match analysis.

        Args:
            data:
                binary MARC data as a `bytes` object.
            matchpoints:
                A dictionary containing matchpoints to be used in matching records.
            template_data:
                Order template data as a dictionary.
            file_name:
                the name of the file being processed.
            handler:
                a `ProcessingHandler` object used by the command.
        Returns:
            A `ProcessedOrderMarcFile` object containing the processed records,
            the file name and the processing statistics
        """
        records = marc_services.BibParser.parse_marc_data(
            data=data,
            engine=handler.engine,
            vendor=template_data.get("vendor", "UNKNOWN"),
        )
        marc_services.BarcodeValidator.ensure_unique(records)
        for bib in records:
            matches = handler.match_service.match_order_record(
                bib, matchpoints=matchpoints
            )
            analysis = bib.analyze_matches(candidates=matches)
            bib.apply_match(analysis)
            marc_services.BibUpdater.update_record(
                bib, engine=handler.engine, template_data=template_data
            )
        return bibs.ProcessedMarcFile(records=records, file_name=file_name)
