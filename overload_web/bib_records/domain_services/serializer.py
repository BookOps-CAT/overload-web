"""Domain service for updating bib records using specific rules.

Classes:

`BibSerializer`
    a domain service that updates records using an injected `BibUpdater`.
"""

from __future__ import annotations

import io
import logging
from typing import Any, BinaryIO, Literal, Optional, overload

from overload_web.bib_records.domain import bibs, marc_protocols
from overload_web.errors import OverloadError

logger = logging.getLogger(__name__)


class BibSerializer:
    """
    Domain service for updating a bib record based on its record type.

    The service updates the `DomainBib` instance with the matched bib ID
    and then updates the record using an injected `BibUpdater` object.
    """

    def __init__(
        self,
        serializer: marc_protocols.BibUpdater,
    ) -> None:
        """
        Initialize the serializer service with an updater.

        Args:
            serializer: An injected `MarcUpdater` that updates bib records.
        """
        self.serializer = serializer

    @overload
    def update(
        self,
        records: list[bibs.DomainBib],
        record_type: Literal[bibs.RecordType.SELECTION],
        template_data: Optional[dict[str, Any]] = None,
    ) -> list[bibs.DomainBib]: ...  # pragma: no branch

    @overload
    def update(
        self,
        records: list[bibs.DomainBib],
        record_type: Literal[bibs.RecordType.CATALOGING],
        template_data: Optional[dict[str, Any]] = None,
    ) -> list[bibs.DomainBib]: ...  # pragma: no branch

    @overload
    def update(
        self,
        records: list[bibs.DomainBib],
        record_type: Literal[bibs.RecordType.ACQUISITIONS],
        template_data: Optional[dict[str, Any]] = None,
    ) -> list[bibs.DomainBib]: ...  # pragma: no branch

    def update(
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
                case bibs.RecordType.ACQUISITIONS if template_data:
                    rec = self.serializer.update_acquisitions_record(
                        record=record, template_data=template_data
                    )
                case bibs.RecordType.SELECTION if template_data:
                    rec = self.serializer.update_selection_record(
                        record=record, template_data=template_data
                    )
                case bibs.RecordType.CATALOGING if record.vendor_info:
                    rec = self.serializer.update_cataloging_record(record=record)
                case bibs.RecordType.CATALOGING if not record.vendor_info:
                    raise OverloadError(
                        "Vendor index required for cataloging workflow."
                    )
                case _:
                    raise OverloadError(
                        "Order template required for acquisition or selection workflow."
                    )
            out.append(rec)
        return out

    def serialize(self, records: list[bibs.DomainBib]) -> BinaryIO:
        """
        Serialize a list of `bibs.DomainBib` objects into a binary MARC stream.

        Args:
            records: a list of records as `bibs.DomainBib` objects

        Returns:
            MARC binary as an an in-memory file stream.
        """
        io_data = io.BytesIO()
        for record in records:
            logger.info(f"Writing MARC binary for record: {record.__dict__}")
            io_data.write(record.binary_data)
        io_data.seek(0)
        return io_data
