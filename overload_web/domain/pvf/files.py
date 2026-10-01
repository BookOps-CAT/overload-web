"""Domain models that define of vendor-supplied MARC files.

Classes:

`IncomingFile`
    Represents a file uploaded to a processing workflow.

`VendorFile`
    Represents a vendor file.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(kw_only=True)
class IncomingFile:
    """
    Represents an incoming file uploaded to Overload.

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
    """
    Represents a file retrieved from a vendor's FTP server.

    Attributes:
        content: binary content of the file.
        file_name: name of the file.
    """

    content: bytes
    file_name: str
