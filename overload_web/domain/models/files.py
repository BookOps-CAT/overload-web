"""Domain models that define of vendor-supplied MARC files.

Classes:

`VendorFile`
    Represents a vendor file.
"""

from __future__ import annotations

from dataclasses import dataclass

from overload_web.shared import schemas


@dataclass(kw_only=True)
class VendorFile(schemas._VendorFile):
    """
    Represents a vendor file.

    Attributes:
        content: binary content of the file.
        file_name: name of the file.
    """

    content: bytes
    file_name: str
