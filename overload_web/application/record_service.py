"""Application services for processing files containing bibliographic records.

This module defines record processing services for full and order-level MARC records.
The services each take `BibFetcher`, `BibMapper`, `MatchAnalyzer`, and
`MarcUpdateHandler` objects as args and have an additional `serializer` attribute.

Classes:

`FullRecordProcessingService`
    An application service for processing full-level MARC records. This service can be
    used to process MARC records following the cataloging workflow (ie. records
    containing `acq` or `sel` as the value for their `record_type` attribute).

`OrderRecordProcessingService`
    An application service for processing order-level MARC records. This service can be
    used to process records following the acquisitions or selection workflows (ie.
    records containing `cat` as the value for their `record_type` attribute).
"""

import itertools
import logging
from typing import Any, BinaryIO

from overload_web.bib_records.domain_services import (
    match,
    parse,
    review,
    serialize,
    update,
)

logger = logging.getLogger(__name__)


class MatchAnalyzerFactory:
    """Create a `MatchAnalyzer` based on `library`, `record_type` and `collection`"""

    def make(
        self, library: str, record_type: str, collection: str
    ) -> review.MatchAnalyzer:
        match record_type, library, collection:
            case "cat", "nypl", "BL":
                return review.NYPLCatBranchMatchAnalyzer()
            case "cat", "nypl", "RL":
                return review.NYPLCatResearchMatchAnalyzer()
            case "cat", "bpl", _:
                return review.BPLCatMatchAnalyzer()
            case "sel", _, _:
                return review.SelectionMatchAnalyzer()
            case _:
                return review.AcquisitionsMatchAnalyzer()


class FullRecordProcessingService:
    """Handles MARC record parsing, matching, and serialization."""

    def __init__(
        self,
        bib_fetcher: match.BibFetcher,
        bib_mapper: parse.BibMapper,
        match_analyzer: review.MatchAnalyzer,
        update_handler: update.MarcUpdateHandler,
    ):
        """
        Initialize `FullRecordProcessingService`.

        Args:
            bib_fetcher:
                A `match.BibFetcher` object
            bib_mapper:
                A `parse.BibMapper` object
            match_analyzer:
                A `review.MatchAnalyzer` object
            update_handler:
                A `update.MarcUpdateHandler` object
        """
        self.reviewer = match_analyzer
        self.matcher = match.FullLevelBibMatcher(fetcher=bib_fetcher)
        self.parser = parse.FullLevelBibParser(mapper=bib_mapper)
        self.updater = update.FullLevelBibUpdater(update_handler=update_handler)
        self.serializer = serialize.FullLevelBibSerializer()

    def process_vendor_file(self, data: BinaryIO | bytes) -> dict[str, BinaryIO]:
        """
        Process a file of full MARC records.

        This service parses full MARC records, matches them against Sierra, analyzes
        all bibs that were returned as matches, updates the records with required
        fields, validates the output, and writes the output to MARC binary.

        Args:
            data: Binary MARC data as a `BinaryIO` or `bytes` object.
        Returns:
            A dictionary containing the file type and an in-memory file stream
            for each type of file to be written. The keys for this dictionary
            will be appended to the file name when writing the binary data to a file.
        """
        parsed_records = self.parser.parse(data=data)
        barcodes = list(
            itertools.chain.from_iterable([i.barcodes for i in parsed_records])
        )
        matched_records = self.matcher.match(records=parsed_records)
        matched_analysis, attached_records = self.reviewer.review_candidates(
            candidates=matched_records
        )
        updated_records = self.updater.update(records=attached_records)
        deduped_records = self.updater.dedupe(
            records=updated_records, reports=matched_analysis
        )
        self.updater.validate(record_batches=deduped_records, barcodes=barcodes)
        serialized_records = self.serializer.serialize(record_batches=deduped_records)
        return serialized_records


class OrderRecordProcessingService:
    """Handles MARC record parsing, matching, and serialization."""

    def __init__(
        self,
        bib_fetcher: match.BibFetcher,
        bib_mapper: parse.BibMapper,
        match_analyzer: review.MatchAnalyzer,
        rules: dict[str, Any],
        update_handler: update.MarcUpdateHandler,
    ):
        """
        Initialize `OrderRecordProcessingService`.

        Args:
            bib_fetcher:
                A `match.BibFetcher` object
            bib_mapper:
                A `parse.BibMapper` object
            match_analyzer:
                A `review.MatchAnalyzer` object
            rules:
                A set of rules to be used by the `MarcUpdateHandler` as a dict
            update_handler:
                A `update.MarcUpdateHandler` object
        """
        self.reviewer = match_analyzer
        self.matcher = match.OrderLevelBibMatcher(fetcher=bib_fetcher)
        self.parser = parse.OrderLevelBibParser(mapper=bib_mapper)
        self.updater = update.OrderLevelBibUpdater(
            rules=rules, update_handler=update_handler
        )
        self.serializer = serialize.OrderLevelBibSerializer()

    def process_vendor_file(
        self,
        data: BinaryIO | bytes,
        matchpoints: dict[str, str],
        template_data: dict[str, Any],
    ) -> BinaryIO:
        """
        Process a file of full MARC records.

        This service parses full MARC records, matches them against Sierra, analyzes
        all bibs that were returned as matches, updates the records with required
        fields, validates the output, and writes the output to MARC binary.

        Args:
            data:
                Binary MARC data as a `BinaryIO` or `bytes` object.
            matchpoints:
                A dictionary containing matchpoints to be used in matching records.
            template_data:
                Order template data as a dictionary.

        Returns:
            MARC data as a `BinaryIO` object
        """
        parsed_records = self.parser.parse(data=data)
        matched_records = self.matcher.match(
            records=parsed_records, matchpoints=matchpoints
        )
        matched_analysis, attached_records = self.reviewer.review_candidates(
            candidates=matched_records
        )
        updated_records = self.updater.update(
            records=attached_records, template_data=template_data
        )
        output = self.serializer.serialize(updated_records)
        return output
