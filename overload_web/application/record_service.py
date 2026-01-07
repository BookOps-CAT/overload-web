"""Application services for processing files containing bibliographic records.

This module defines record processing services for Full and Order-level MARC records.
The service takes a `collection`, `BibFetcher`, `BibMapper`, and `BibUpdate` as args and
has `collection`, `parser`, and `matcher` attributes. The `parser` attribute is a
`BibParser` domain object and contains a concrete implementation of the `BibMapper`
domain protocol. The `matcher` attribute is a `BibMatcher` domain object and contains
a concrete implementation of the `BibFetcher` domain protocol.

Classes:

`FullRecordProcessingService`
    An application service for processing full-level MARC records. This service can be
    used to process MARC records following the cataloging workflow.

`OrderRecordProcessingService`
    An application service for processing order-level MARC records. This service can be
    used to process records following the acquisitions or selection workflows.
"""

import logging
from typing import Any, BinaryIO

from overload_web.bib_records.domain_models import (
    marc_protocols,
)
from overload_web.bib_records.domain_services import (
    match,
    parse,
    review,
    update,
)

logger = logging.getLogger(__name__)


class MatchPolicyFactory:
    def make(
        self, library: str, record_type: str, collection: str
    ) -> marc_protocols.BibMatchPolicy:
        match record_type, library, collection:
            case "cat", "nypl", "BL":
                return review.NYPLCatBranchMatchPolicy()
            case "cat", "nypl", "RL":
                return review.NYPLCatResearchMatchPolicy()
            case "cat", "bpl", _:
                return review.BPLCatMatchPolicy()
            case "sel", _, _:
                return review.SelectionMatchPolicy()
            case _:
                return review.AcquisitionsMatchPolicy()


class FullRecordProcessingService:
    """Handles MARC record parsing, matching, and serialization."""

    def __init__(
        self,
        bib_fetcher: marc_protocols.BibFetcher,
        bib_mapper: marc_protocols.BibMapper,
        match_policy: marc_protocols.BibMatchPolicy,
        update_handler: marc_protocols.MarcUpdateHandler,
    ):
        """
        Initialize `FullRecordProcessingService`.

        Args:
            bib_fetcher:
                A `marc_protocols.BibFetcher` object
            bib_mapper:
                A `marc_protocols.BibMapper` object
            match_policy:
                A `marc_protocols.BibMatchPolicy` object
            update_handler:
                A `marc_protocols.BibUpdater` object
        """
        self.reviewer = review.BibReviewer(policy=match_policy)
        self.matcher = match.FullLevelBibMatcher(fetcher=bib_fetcher)
        self.parser = parse.FullLevelBibParser(mapper=bib_mapper)
        self.serializer = update.FullLevelBibUpdater(update_handler=update_handler)

    def process_vendor_file(self, data: BinaryIO | bytes) -> BinaryIO:
        """
        Parse MARC records, match them against Sierra, update the records with required
        fields and write them to MARC binary.

        Args:
            data: Binary MARC data as a `BinaryIO` or `bytes` object.
        Returns:
            MARC data as a `BinaryIO` object
        """
        parsed_records, barcodes = self.parser.parse(data=data)
        matched_records = self.matcher.match(records=parsed_records)
        matched_analysis, attached_records = self.reviewer.review_candidates(
            candidates=matched_records
        )
        updated_records = self.serializer.update(records=attached_records)
        output = self.serializer.serialize(updated_records)
        return output


class OrderRecordProcessingService:
    """Handles MARC record parsing, matching, and serialization."""

    def __init__(
        self,
        bib_fetcher: marc_protocols.BibFetcher,
        bib_mapper: marc_protocols.BibMapper,
        match_policy: marc_protocols.BibMatchPolicy,
        rules: dict[str, Any],
        update_handler: marc_protocols.MarcUpdateHandler,
    ):
        """
        Initialize `OrderRecordProcessingService`.

        Args:
            bib_fetcher:
                A `marc_protocols.BibFetcher` object
            bib_mapper:
                A `marc_protocols.BibMapper` object
            match_policy:
                A `marc_protocols.BibMatchPolicy` object
            rules:
                A set of rules to be used by the `BibUpdater` as a dict
            update_handler:
                A `marc_protocols.BibUpdater` object
        """
        self.reviewer = review.BibReviewer(policy=match_policy)
        self.matcher = match.OrderLevelBibMatcher(fetcher=bib_fetcher)
        self.parser = parse.OrderLevelBibParser(mapper=bib_mapper)
        self.serializer = update.OrderLevelBibUpdater(
            rules=rules, update_handler=update_handler
        )

    def process_vendor_file(
        self,
        data: BinaryIO | bytes,
        matchpoints: dict[str, str],
        template_data: dict[str, Any],
    ) -> BinaryIO:
        """
        Parse MARC records, match them against Sierra, update the records with required
        fields and write them to MARC binary.

        Args:
            data: Binary MARC data as a `BinaryIO` or `bytes` object.
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
        updated_records = self.serializer.update(
            records=attached_records, template_data=template_data
        )
        output = self.serializer.serialize(updated_records)
        return output
