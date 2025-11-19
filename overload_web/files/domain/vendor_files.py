"""Domain models that define files of vendor-supplied MARC records"""

from __future__ import annotations

from dataclasses import dataclass

from overload_web.shared import schemas


@dataclass(kw_only=True)
class VendorFile(schemas.FileData):
    """
    Represents a vendor file.

    Attributes:
        content: binary content of the file.
        file_name: name of the file.
    """

    content: bytes
    file_name: str
