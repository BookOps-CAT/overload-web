"""Domain models that define files of vendor-supplied MARC records"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(kw_only=True)
class VendorFile:
    """
    Represents a vendor file.
    Attributes:
        library: the library to whom the file belongs.
        file_name: name of the file.
        content: binary content of the file.
        id: the unique identifier for the file
    """

    library: str
    file_name: str
    content: bytes
    id: Optional[VendorFileId] = None


@dataclass
class VendorFileId:
    """A dataclass to define a VendorFileId as an entity"""

    value: str
