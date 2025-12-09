"""Domain service for updating bib records using specific rules.

Classes:

`BibRecordUpdater`
    a domain service that updates records using an injected `BibUpdateStrategy`.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from overload_web.bib_records.domain import bibs, marc_protocols

logger = logging.getLogger(__name__)


class BibRecordUpdater:
    """
    Domain service for updating a bib record based on its record type.

    The service updates the `DomainBib` instance with the matched bib ID
    and then updates the record using an injected `BibUpdateStrategy` object.
    """

    def __init__(self, strategy: marc_protocols.BibUpdateStrategy) -> None:
        """
        Initialize the serializer service with an updater.

        Args:
            strategy: An injected `BibUpdateStrategy` that updates bib records.
        """
        self.strategy = strategy

    def update(
        self,
        records: list[bibs.DomainBib],
        template_data: Optional[dict[str, Any]] = None,
    ) -> list[bibs.DomainBib]:
        """
        Update bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.
            template_data:
                A dictionary containing template data to be used in updating records.

        Returns:
            A list of updated records as `bibs.DomainBib` objects
        """
        out = self.strategy.update_bib(records=records, template_data=template_data)
        return out
