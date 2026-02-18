"""Application services for processing files containing bibliographic records.

Classes:

`ProcessingHandler`
    An application service for processing MARC records. This service is passed to
    the application commands `ProcessFullRecords` and `ProcessOrderRecords`
"""

from __future__ import annotations

import logging

from overload_web.application import ports
from overload_web.application.services import match_service

logger = logging.getLogger(__name__)


class ProcessingHandler:
    """Handles parsing, matching, and analysis of full-level MARC records."""

    def __init__(
        self,
        fetcher: ports.BibFetcher,
        engine: ports.MarcEnginePort,
    ):
        """
        Initialize `ProcessingHandler`.

        Args:
            fetcher:
                A `match_service.BibFetcher` object
            engine:
                A `ports.MarcEnginePort` object
        """
        self.match_service = match_service.BibMatcher(fetcher=fetcher)
        self.engine = engine
