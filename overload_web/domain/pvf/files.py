"""Domain models that define vendor-supplied MARC files.

Classes:

`IncomingFile`
    Represents a file uploaded to a processing workflow.

`VendorFile`
    Represents a vendor file during processing.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass


@dataclass(kw_only=True)
class IncomingFile:
    """Represents an incoming file uploaded to Overload.

    Attributes:
        filename: name of the file.
        id: the ID for the file
        reference: the file path where the file has been saved.
        source: either `'ftp'` or `'local'` indicating the source of the file
        workflow_id: the shared ID for the file and others a part of the workflow

    """

    filename: str
    id: str
    source: str
    reference: str
    workflow_id: str


@dataclass(kw_only=True)
class VendorFile:
    """Represents a file retrieved from a vendor's FTP server.

    Attributes:
        content: binary content of the file.
        filename: name of the file.

    """

    content: bytes
    filename: str


@dataclass(kw_only=True)
class VendorFileInfo:
    """Represents metadata for a file retrieved from a vendor's FTP server.

    Attributes:
        filename: name of the file.
        size: the file size in bytes
        update_date: the last update date for the file as a timestamp int

    """

    filename: str
    size: int
    update_date: int

    @property
    def formatted_bytes(self) -> str:
        """Bytes formatted as a string."""
        return f"{self.size / 1024:.2f} KB"

    @property
    def update_date_str(self) -> str:
        """Update date of file as a string (MM-DD-YYYY HH:MM PM)."""
        datetime_stamp = datetime.datetime.fromtimestamp(
            self.update_date, tz=datetime.UTC
        )
        return datetime.datetime.strftime(datetime_stamp, "%m-%d-%Y %I:%M %p")
