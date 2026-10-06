from __future__ import annotations

from enum import StrEnum


class Message:
    pass


class Command(Message):
    pass


class Event(Message):
    pass


class Collection(StrEnum):
    """Valid values for NYPL and BPL collections"""

    BRANCH = "BL"
    RESEARCH = "RL"
    MIXED = "MIXED"
    NONE = "NONE"


class LibrarySystem(StrEnum):
    """Valid values for library system"""

    BPL = "bpl"
    NYPL = "nypl"


class RecordType(StrEnum):
    """Valid values for record type/processing workflow."""

    ACQUISITIONS = "acq"
    CATALOGING = "cat"
    SELECTION = "sel"
