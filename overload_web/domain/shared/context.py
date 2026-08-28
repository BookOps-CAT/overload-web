"""Domain models that define shared component parts."""

from __future__ import annotations

import logging
from enum import StrEnum

logger = logging.getLogger(__name__)


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
