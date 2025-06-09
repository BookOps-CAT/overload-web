from __future__ import annotations

from dataclasses import dataclass

from overload_web.domain import models


@dataclass
class FileContentDTO:
    """
    Data Transfer Object representing a file's content.

    Attributes:
        file_id: Unique identifier for the file.
        content: Raw binary content for the file.
    """

    file_id: str
    content: bytes

    def to_domain(self, file_name: FileMetadataDTO) -> models.files.VendorFile:
        if not file_name.file_id == self.file_id:
            raise ValueError("File metadata and content are not for the same object")
        return models.files.VendorFile(
            id=models.files.VendorFileId(value=self.file_id),
            file_name=file_name.name,
            content=self.content,
        )


@dataclass
class FileMetadataDTO:
    """
    Data Transfer Object representing metadata about a file.

    Attributes:
        file_id: Unique identifier for the file.
        name: The name of the file as a string.
    """

    file_id: str
    name: str

    def to_domain(self, file_content: FileContentDTO) -> models.files.VendorFile:
        if not file_content.file_id == self.file_id:
            raise ValueError("File metadata and content are not for the same object")
        return models.files.VendorFile(
            id=models.files.VendorFileId(value=self.file_id),
            file_name=self.name,
            content=file_content.content,
        )
