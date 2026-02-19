import logging
from typing import Any, Sequence

from overload_web.application import ports
from overload_web.application.services import marc_services, record_service
from overload_web.domain.models import files, reports, templates

logger = logging.getLogger(__name__)


class ProcessFullRecords:
    """Handles parsing, matching, and analysis of full MARC records."""

    @staticmethod
    def execute(
        data: bytes, file_name: str, handler: record_service.ProcessingHandler
    ) -> reports.ProcessedFullRecordsBatch:
        """
        Process a file of full MARC records.

        This service parses full MARC records, matches them against Sierra, analyzes
        all bibs that were returned as matches, updates the records with required
        fields, and outputs the updated records and the match_analysis.

        Args:
            data: Binary MARC data as a `bytes` object.
            file_name: the name of the file being processed.
            handler: a `ProcessingHandler` object used by the command.
        Returns:
            A `ProcessedFullRecordsBatch` object containing the processed records,
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

        batches = marc_services.Deduplicator.deduplicate(records, engine=handler.engine)
        missing_barcodes = marc_services.BarcodeValidator.ensure_preserved(
            record_batches=batches, barcodes=barcodes
        )
        out = reports.ProcessedFullRecordsBatch(
            duplicate_records=batches["DUP"],
            duplicate_records_stream=marc_services.BibSerializer.write(batches["DUP"]),
            new_records=batches["NEW"],
            new_records_stream=marc_services.BibSerializer.write(batches["NEW"]),
            deduplicated_records=batches["DEDUPED"],
            deduplicated_records_stream=marc_services.BibSerializer.write(
                batches["DEDUPED"]
            ),
            missing_barcodes=missing_barcodes,
            file_name=file_name,
            library=handler.engine.library,
            record_type=handler.engine.record_type,
            collection=handler.engine.collection,
        )
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
    ) -> reports.ProcessedOrderRecordsBatch:
        """
        Process a file of order-level MARC records.

        This service parses order-level MARC records, matches them against Sierra,
        analyzes all bibs that were returned as matches, updates the records with
        required fields, and outputs the updated records and the match_analysis.

        Args:
            data:
                Binary MARC data as a `bytes` object.
            matchpoints:
                A dictionary containing matchpoints to be used in matching records.
            template_data:
                Order template data as a dictionary.
            file_name:
                the name of the file being processed.
            handler:
                a `ProcessingHandler` object used by the command.
        Returns:
            A `ProcessedOrderRecordsBatch` object containing the processed records,
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

        stream = marc_services.BibSerializer.write(records)
        return reports.ProcessedOrderRecordsBatch(
            records=records,
            record_stream=stream,
            file_name=file_name,
            library=handler.engine.library,
            record_type=handler.engine.record_type,
            collection=handler.engine.collection,
        )


class CreateOrderTemplate:
    @staticmethod
    def execute(
        repository: ports.SqlRepositoryProtocol, obj: templates.OrderTemplateBase
    ) -> templates.OrderTemplate:
        """
        Save an order template.

        Args:
            repository: a `ports.SqlRepositoryProtocol` object.
            obj: the template data as an `OrderTemplateBase` object.

        Raises:
            ValidationError: If the template lacks a name, agent, or primary_matchpoint.

        Returns:
            The saved template as an `OrderTemplate` object.
        """
        save_template = repository.save(obj=obj)
        return templates.OrderTemplate(**save_template.model_dump())


class GetOrderTemplate:
    @staticmethod
    def execute(
        repository: ports.SqlRepositoryProtocol, template_id: str
    ) -> templates.OrderTemplate | None:
        """
        Retrieve an order template by its ID.

        Args:
            repository: a `ports.SqlRepositoryProtocol` object.
            template_id: unique identifier for the template.

        Returns:
            The retrieved template as a `OrderTemplate` object or None.
        """
        return repository.get(id=template_id)


class ListOrderTemplates:
    @staticmethod
    def execute(
        repository: ports.SqlRepositoryProtocol,
        offset: int | None = 0,
        limit: int | None = 20,
    ) -> Sequence[templates.OrderTemplate]:
        """
        Retrieve a list of templates in the database.

        Args:
            repository: a `ports.SqlRepositoryProtocol` object.
            offset: start position of first `OrderTemplate` object to return.
            limit: the maximum number of `OrderTemplate` objects to return.

        Returns:
            A list of `OrderTemplate` objects.
        """
        return repository.list(offset=offset, limit=limit)


class UpdateOrderTemplate:
    @staticmethod
    def execute(
        repository: ports.SqlRepositoryProtocol,
        template_id: str,
        obj: templates.OrderTemplateBase,
    ) -> templates.OrderTemplate | None:
        """
        Update an existing order template.

        Args:
            repository: a `ports.SqlRepositoryProtocol` object.
            template_id: unique identifier for the template to be updated.
            obj: the data to be replaces as an `OrderTemplateBase` object.

        Returns:
            The updated template as an `OrderTemplate` or None if the template
            does not exist.
        """
        return repository.update_template(id=template_id, data=obj)


class ListVendorFiles:
    @staticmethod
    def execute(dir: str, loader: ports.FileLoader) -> list[str]:
        """
        List files in a directory.

        Args:
            dir: The directory whose files to list.
            loader: concrete implementation of `FileLoader` protocol
        Returns:
            a list of filenames contained within the given directory as strings.
        """
        files = loader.list(dir=dir)
        logger.info(f"Files in {dir}: {files}")
        return files


class LoadVendorFile:
    @staticmethod
    def execute(name: str, dir: str, loader: ports.FileLoader) -> files.VendorFile:
        """
        Load a file from a directory.

        Args:
            name: The name of the file as a string.
            dir: The directory where the file is located.
            loader: concrete implementation of `FileLoader` protocol

        Returns:
            The loaded file as a `files.VendorFile` object.
        """
        file = loader.load(name=name, dir=dir)
        logger.info(f"File loaded: {name}")
        return file


class WriteFile:
    @staticmethod
    def execute(file: files.VendorFile, dir: str, writer: ports.FileWriter) -> str:
        """
        Write a file to a directory.

        Args:
            file: The file to write as a `files.VendorFile` object.
            dir: The directory where the file should be written.
            writer: concrete implementation of `FileWriter` protocol

        Returns:
            the directory and filename where the file was written.
        """
        out_file = writer.write(file=file, dir=dir)
        logger.info(f"Writing file to directory: {dir}/{out_file}")
        return out_file


class CreateFullRecordsProcessingReport:
    @staticmethod
    def execute(
        report_data: list[reports.ProcessedFullRecordsBatch],
        handler: ports.ReportHandler,
    ) -> reports.ProcessingStatistics:
        file_names = [i.file_name for i in report_data]
        all_recs = []
        missing_barcodes = []
        for report in report_data:
            all_recs.extend(report.duplicate_records)
            all_recs.extend(report.new_records)
            missing_barcodes.extend(report.missing_barcodes)
        data_dict = handler.list2dict(all_recs)
        return reports.ProcessingStatistics(
            summary=handler.create_summary_report(
                file_names=file_names,
                total_files_processed=len(file_names),
                total_records_processed=len(all_recs),
                missing_barcodes=missing_barcodes,
                report_data=data_dict,
            ),
            detailed_data=handler.create_detailed_report(data_dict),
        )


class CreateOrderRecordsProcessingReport:
    @staticmethod
    def execute(
        report_data: list[reports.ProcessedOrderRecordsBatch],
        handler: ports.ReportHandler,
    ) -> reports.ProcessingStatistics:
        file_names = [i.file_name for i in report_data]
        all_recs = []
        for report in report_data:
            all_recs.extend(report.records)
        data_dict = handler.list2dict(all_recs)
        return reports.ProcessingStatistics(
            summary=handler.create_summary_report(
                file_names=file_names,
                total_files_processed=len(file_names),
                total_records_processed=len(all_recs),
                report_data=data_dict,
            ),
            detailed_data=handler.create_detailed_report(data_dict),
        )
