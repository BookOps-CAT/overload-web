"""Shared domain objects used within Overload."""

from __future__ import annotations

from enum import StrEnum


class Message:
    """Base class for Commands and Events."""

    pass


class Command(Message):
    """Base class for all commands."""

    pass


class Event(Message):
    """Base class for all events."""

    pass


class Collection(StrEnum):
    """Valid values for NYPL and BPL collections."""

    BRANCH = "BL"
    RESEARCH = "RL"
    MIXED = "MIXED"
    NONE = "NONE"


class LibrarySystem(StrEnum):
    """Valid values for library system."""

    BPL = "bpl"
    NYPL = "nypl"


class RecordType(StrEnum):
    """Valid values for record type/processing workflow."""

    ACQUISITIONS = "acq"
    CATALOGING = "cat"
    SELECTION = "sel"
