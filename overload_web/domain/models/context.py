"""Domain models that define context value objects"""

from __future__ import annotations

from enum import Enum


class Collection(Enum):
    """Includes valid values for NYPL collection"""

    BRANCH = "BL"
    RESEARCH = "RL"

    def __str__(self):
        return self.value


class LibrarySystem(Enum):
    """Includes valid values for library system"""

    BPL = "bpl"
    NYPL = "nypl"

    def __str__(self):
        return self.value


class RecordType(Enum):
    """Includes valid values for record type"""

    FULL = "full"
    ORDER_LEVEL = "order_level"

    def __str__(self):
        return self.value
