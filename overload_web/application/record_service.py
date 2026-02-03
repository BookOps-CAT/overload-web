"""Application services for processing files containing bibliographic records.

This module defines record processing services for full and order-level MARC records.
The services each take `BibFetcher`, `BibMapper`, `MatchAnalyzer`, and
`BibUpdater` objects as args.

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

import logging
from typing import Any, BinaryIO

from overload_web.domain.services import analysis, match, parse, update

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
    """Handles parsing, matching, and analysis of full-level MARC records."""

    def __init__(
        self,
        bib_fetcher: match.BibFetcher,
        bib_mapper: parse.BibMapper,
        analyzer: analysis.MatchAnalyzer,
        update_strategy: update.MarcUpdateStrategy,
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
            update_strategy:
                An `update.MarcUpdateStrategy` object
        """
        self.analyzer = analyzer
        self.matcher = match.FullLevelBibMatcher(fetcher=bib_fetcher)
        self.parser = parse.BibParser(mapper=bib_mapper)
        self.updater = update.BibUpdater(strategy=update_strategy)

    def process_vendor_file(self, data: BinaryIO | bytes) -> dict[str, Any]:
        """
        Process a file of full MARC records.

        This service parses full MARC records, matches them against Sierra, analyzes
        all bibs that were returned as matches, updates the records with required
        fields, and outputs the updated records and the analysis.

        Args:
            data: Binary MARC data as a `BinaryIO` or `bytes` object.
        Returns:
            A dictionary containing the a list of processed records as `DomainBib`
            objects and the the `ProcessVendorFileReport` for the file of records.
        """
        parsed_records = self.parser.parse(data=data)
        barcodes = self.parser.extract_barcodes(parsed_records)
        out: dict[str, list[Any]] = {"records": [], "report": [], "barcodes": barcodes}
        for record in parsed_records:
            candidates = self.matcher.match(record=record)
            analysis = self.analyzer.analyze_match(record=record, candidates=candidates)
            out["report"].append(analysis)
            record.apply_match_decision(analysis.decision)
            updated = self.updater.update(record=record)
            out["records"].append(updated)
        return out


class OrderRecordProcessingService:
    """Handles parsing, matching, and analysis of order-level MARC records."""

    def __init__(
        self,
        bib_fetcher: match.BibFetcher,
        bib_mapper: parse.BibMapper,
        analyzer: analysis.MatchAnalyzer,
        update_strategy: update.MarcUpdateStrategy,
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
            update_strategy:
                An `update.MarcUpdateStrategy` object
        """
        self.analyzer = analyzer
        self.matcher = match.OrderLevelBibMatcher(fetcher=bib_fetcher)
        self.parser = parse.BibParser(mapper=bib_mapper)
        self.updater = update.BibUpdater(strategy=update_strategy)

    def process_vendor_file(
        self,
        data: BinaryIO | bytes,
        matchpoints: dict[str, str],
        template_data: dict[str, Any],
        vendor: str | None = None,
    ) -> dict[str, Any]:
        """
        Process a file of full MARC records.

        This service parses full MARC records, matches them against Sierra, analyzes
        all bibs that were returned as matches, updates the records with required
        fields, and outputs the updated records and the analysis.

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
            A dictionary containing the a list of processed records as `DomainBib`
            objects and the the `ProcessVendorFileReport` for the file of records.
        """
        parsed_records = self.parser.parse(data=data, vendor=vendor)
        out: dict[str, list[Any]] = {"records": [], "report": []}
        for record in parsed_records:
            candidates = self.matcher.match(record=record, matchpoints=matchpoints)
            analysis = self.analyzer.analyze_match(record=record, candidates=candidates)
            out["report"].append(analysis)
            record.apply_match_decision(analysis.decision)
            updated = self.updater.update(record=record, template_data=template_data)
            out["records"].append(updated)
        return out
