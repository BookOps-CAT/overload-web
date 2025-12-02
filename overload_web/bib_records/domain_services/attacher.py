"""Domain service for updating bib records using specific rules.

Classes:

`BibAttacher`
    a domain service that updates records using an injected `BibUpdater`.
"""

from __future__ import annotations

import logging
from typing import Any, Literal, Optional, overload

from overload_web.bib_records.domain import bibs, marc_protocols
from overload_web.errors import OverloadError

logger = logging.getLogger(__name__)


class BibAttacher:
    """
    Domain service for updating a bib record based on its record type.

    The service updates the `DomainBib` instance with the matched bib ID
    and then updates the record using an injected `BibUpdater` object.
    """

    def __init__(
        self,
        attacher: marc_protocols.BibUpdater,
    ) -> None:
        """
        Initialize the attacher service with an updater.

        Args:
            attacher: An injected `MarcUpdater` that updates bib records.
        """
        self.attacher = attacher

    def _attach_acq(
        self,
        record: bibs.DomainBib,
        template_data: dict[str, Any],
    ) -> bibs.DomainBib:
        return self.attacher.update_acquisitions_record(
            record=record, template_data=template_data
        )

    def _attach_cat(self, record: bibs.DomainBib) -> bibs.DomainBib:
        if not record.vendor_info:
            raise OverloadError("Vendor index required for cataloging workflow.")
        return self.attacher.update_cataloging_record(record=record)

    def _attach_sel(
        self,
        record: bibs.DomainBib,
        template_data: dict[str, Any],
    ) -> bibs.DomainBib:
        return self.attacher.update_selection_record(
            record=record, template_data=template_data
        )

    @overload
    def attach(
        self,
        records: list[bibs.DomainBib],
        record_type: Literal[bibs.RecordType.SELECTION],
        template_data: Optional[dict[str, Any]] = None,
    ) -> list[bibs.DomainBib]: ...  # pragma: no branch

    @overload
    def attach(
        self,
        records: list[bibs.DomainBib],
        record_type: Literal[bibs.RecordType.CATALOGING],
        template_data: Optional[dict[str, Any]] = None,
    ) -> list[bibs.DomainBib]: ...  # pragma: no branch

    @overload
    def attach(
        self,
        records: list[bibs.DomainBib],
        record_type: Literal[bibs.RecordType.ACQUISITIONS],
        template_data: Optional[dict[str, Any]] = None,
    ) -> list[bibs.DomainBib]: ...  # pragma: no branch

    def attach(
        self,
        records: list[bibs.DomainBib],
        record_type: bibs.RecordType,
        template_data: Optional[dict[str, Any]] = None,
    ) -> list[bibs.DomainBib]:
        """
        Update bibliographic records.

        Args:
            records:
                A list of parsed bibliographic records as `bibs.DomainBib` objects.
            template_data:
                A dictionary containing template data to be used in updating records.
            record_type:
                The type of record as an Literal value from bibs.RecordType.

        Returns:
            A list of updated records as `bibs.DomainBib` objects
        """
        out = []
        for record in records:
            match record_type:
                case bibs.RecordType.CATALOGING:
                    rec = self._attach_cat(record=record)
                case bibs.RecordType.ACQUISITIONS if template_data:
                    rec = self._attach_acq(record=record, template_data=template_data)
                case bibs.RecordType.SELECTION if template_data:
                    rec = self._attach_sel(record=record, template_data=template_data)
                case _:
                    raise OverloadError(
                        "Order template required for acquisition or selection workflow."
                    )
            out.append(rec)
        return out
