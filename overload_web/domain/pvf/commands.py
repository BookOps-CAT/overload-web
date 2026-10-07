from dataclasses import dataclass
from typing import Any

from overload_web.domain.shared import Command


@dataclass
class ParseOrderLevelFiles(Command):
    """Command to parse order-level records from incoming files."""

    workflow_id: str
    vendor: str


@dataclass
class MatchOrderLevelRecords(Command):
    """Command to match order-level records after they have been parsed."""

    workflow_id: str
    matchpoints: dict[str, str]


@dataclass
class UpdateAndOutputOrderLevelRecords(Command):
    """Command to update and output order-level records."""

    workflow_id: str
    template_data: dict[str, Any]


@dataclass
class ParseFullLevelFiles(Command):
    """Command to parse full MARC records from incoming files."""

    workflow_id: str


@dataclass
class MatchFullLevelRecords(Command):
    """Command to match full MARC records after they have been parsed."""

    workflow_id: str


@dataclass
class UpdateAndOutputFullLevelRecords(Command):
    """Command to update and output full MARC records."""

    workflow_id: str
