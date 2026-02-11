import logging
from typing import Any, BinaryIO, Sequence

from overload_web.application import ports
from overload_web.application.services import (
    marc_services,
    record_service,
    report_service,
)
from overload_web.domain.models import files, rules, templates

logger = logging.getLogger(__name__)


class ProcessFullRecords:
    """Handles parsing, matching, and analysis of full MARC records."""

    @staticmethod
    def execute(
        data: BinaryIO | bytes,
        file_name: str,
        handler: record_service.ProcessingHandler,
    ) -> tuple:
        """
        Process a file of full MARC records.

        This service parses full MARC records, matches them against Sierra, analyzes
        all bibs that were returned as matches, updates the records with required
        fields, and outputs the updated records and the match_analysis.

        Args:
            data: Binary MARC data as a `BinaryIO` or `bytes` object.
            file_name: the name of the file being processed.
            handler: a `ProcessingHandler` object used by the command.
        Returns:
            A tuple containing a dictionary of the processed records and their file
            names and the processing statistics
        """
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


class ProcessOrderRecords:
    """Handles parsing, matching, and analysis of order-level MARC records."""

    @staticmethod
    def execute(
        data: BinaryIO | bytes,
        file_name: str,
        handler: record_service.ProcessingHandler,
        matchpoints: dict[str, str],
        template_data: dict[str, Any],
    ) -> tuple:
        """
        Process a file of order-level MARC records.

        This service parses order-level MARC records, matches them against Sierra,
        analyzes all bibs that were returned as matches, updates the records with
        required fields, and outputs the updated records and the match_analysis.

        Args:
            data:
                Binary MARC data as a `BinaryIO` or `bytes` object.
            matchpoints:
                A dictionary containing matchpoints to be used in matching records.
            template_data:
                Order template data as a dictionary.
            file_name:
                the name of the file being processed.
            handler:
                a `ProcessingHandler` object used by the command.
        Returns:
            A containing the processed records as binary data and the processing
            statistics
        """
        bibs = marc_services.BibParser.parse_marc_data(
            data=data,
            engine=handler.engine,
            vendor=template_data.get("vendor", "UNKNOWN"),
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
        return repository.apply_updates(id=template_id, data=obj)


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
