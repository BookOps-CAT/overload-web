"""Application services for processing files containing bibliographic records.

Classes:

`ProcessingHandler`
    An application service for processing MARC records. This service is passed to
    the application commands `ProcessFullRecords` and `ProcessOrderRecords`
"""

import logging

from overload_web.application import ports
from overload_web.application.services import match_service
from overload_web.domain.services import match_analysis

logger = logging.getLogger(__name__)


class MatchAnalyzerFactory:
    """Create a `MatchAnalyzer` based on `library`, `record_type` and `collection`"""

    def make(
        self, library: str, record_type: str, collection: str
    ) -> match_analysis.MatchAnalyzer:
        match record_type, library, collection:
            case "cat", "nypl", "BL":
                return match_analysis.NYPLCatBranchMatchAnalyzer()
            case "cat", "nypl", "RL":
                return match_analysis.NYPLCatResearchMatchAnalyzer()
            case "cat", "bpl", _:
                return match_analysis.BPLCatMatchAnalyzer()
            case "sel", _, _:
                return match_analysis.SelectionMatchAnalyzer()
            case _:
                return match_analysis.AcquisitionsMatchAnalyzer()


class ProcessingHandler:
    """Handles parsing, matching, and analysis of full-level MARC records."""

    def __init__(
        self,
        fetcher: ports.BibFetcher,
        engine: ports.MarcEnginePort,
        analyzer: match_analysis.MatchAnalyzer,
    ):
        """
        Initialize `ProcessingHandler`.

        Args:
            bib_fetcher:
                A `ports.BibFetcher` object
            analyzer:
                An `match_analysis.MatchAnalyzer` object
            engine:
                An `update.MarcEnginePort` object
        """
        self.analysis_service = analyzer
        self.match_service = match_service.BibMatcher(fetcher=fetcher)
        self.engine = engine
