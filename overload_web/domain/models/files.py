"""Domain models that define files of vendor-supplied MARC records"""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(kw_only=True)
class VendorFile:
    """
    Represents a vendor file.
    Attributes:
        id: the unique identifier for the file.
        content: binary content of the file.
        file_name: name of the file.
    """

    id: VendorFileId
    content: bytes
    file_name: str

    @classmethod
    def create(cls, content: bytes, file_name: str) -> VendorFile:
        """Factory method to enforce ID assignment and domain rules."""
        return cls(id=VendorFileId.new(), content=content, file_name=file_name)


@dataclass(frozen=True)
class VendorFileId:
    """A dataclass to define a `VendorFileId` as an entity"""

    value: str

    def __post_init__(self):
        """Validate that the vendor file ID is a string"""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("VendorFileId must be a non-empty string.")

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"VendorFileId(value={self.value!r})"

    @classmethod
    def new(cls) -> VendorFileId:
        """Create a new ID using UUID4"""
        return cls(value=str(uuid.uuid4()))
