"""Application services for processing files containing bibliographic records.

This module defines record processing services for full and order-level MARC records.
The services each take `BibFetcher`, `BibMapper`, `MatchAnalyzer`, and
`BibUpdater` objects as args and have an additional `serializer` attribute.

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
    analysis,
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
    ) -> analysis.MatchAnalyzer:
        match record_type, library, collection:
            case "cat", "nypl", "BL":
                return analysis.NYPLCatBranchMatchAnalyzer()
            case "cat", "nypl", "RL":
                return analysis.NYPLCatResearchMatchAnalyzer()
            case "cat", "bpl", _:
                return analysis.BPLCatMatchAnalyzer()
            case "sel", _, _:
                return analysis.SelectionMatchAnalyzer()
            case _:
                return analysis.AcquisitionsMatchAnalyzer()


class FullRecordProcessingService:
    """Handles parsing, matching, and serialization of full-level MARC records."""

    def __init__(
        self,
        bib_fetcher: match.BibFetcher,
        bib_mapper: parse.BibMapper,
        analyzer: analysis.MatchAnalyzer,
        updater: update.BibUpdater,
    ):
        """
        Initialize `FullRecordProcessingService`.

        Args:
            bib_fetcher:
                A `match.BibFetcher` object
            bib_mapper:
                A `parse.BibMapper` object
            analyzer:
                An `analysis.MatchAnalyzer` object
            updater:
                An `update.BibUpdater` object
        """
        self.analyzer = analyzer
        self.matcher = match.FullLevelBibMatcher(fetcher=bib_fetcher)
        self.parser = parse.FullLevelBibParser(mapper=bib_mapper)
        self.reviewer = review.FullLevelBibReviewer(context_factory=updater.strategy)
        self.updater = updater
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
        match_analysis = self.analyzer.analyze_matches(candidates=matched_records)
        updated_records = self.updater.update(
            records=[i.updated_domain_bib for i in match_analysis]
        )
        deduped_records = self.reviewer.dedupe(
            records=updated_records, reports=match_analysis
        )
        self.reviewer.validate(record_batches=deduped_records, barcodes=barcodes)
        serialized_records = self.serializer.serialize(record_batches=deduped_records)
        return serialized_records


class OrderRecordProcessingService:
    """Handles parsing, matching, and serialization of order-level MARC records."""

    def __init__(
        self,
        bib_fetcher: match.BibFetcher,
        bib_mapper: parse.BibMapper,
        analyzer: analysis.MatchAnalyzer,
        updater: update.BibUpdater,
    ):
        """
        Initialize `OrderRecordProcessingService`.

        Args:
            bib_fetcher:
                A `match.BibFetcher` object
            bib_mapper:
                A `parse.BibMapper` object
            analyzer:
                An `analysis.MatchAnalyzer` object
            updater:
                An `update.BibUpdater` object
        """
        self.analyzer = analyzer
        self.matcher = match.OrderLevelBibMatcher(fetcher=bib_fetcher)
        self.parser = parse.OrderLevelBibParser(mapper=bib_mapper)
        self.updater = updater
        self.serializer = serialize.OrderLevelBibSerializer()

    def process_vendor_file(
        self,
        data: BinaryIO | bytes,
        matchpoints: dict[str, str],
        template_data: dict[str, Any],
        vendor: str | None,
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
            vendor:
                The vendor whose records are being processed as a string.

        Returns:
            MARC data as a `BinaryIO` object
        """
        parsed_records = self.parser.parse(data=data, vendor=vendor)
        matched_records = self.matcher.match(
            records=parsed_records, matchpoints=matchpoints
        )
        match_analysis = self.analyzer.analyze_matches(candidates=matched_records)
        updated_records = self.updater.update(
            records=[i.updated_domain_bib for i in match_analysis],
            template_data=template_data,
        )
        output = self.serializer.serialize(updated_records)
        return output
