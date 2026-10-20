from dataclasses import dataclass
from typing import Any

from overload_web.domain.shared import Command


@dataclass
class InitializeWorkflow(Command):
    """Command to create a new workflow."""

    workflow_id: str


@dataclass
class StartOrderLevelRecordsWorkflow(Command):
    """Command to start order-level processing workflow."""

    collection: str | None
    library: str
    matchpoints: dict[str, str]
    record_type: str
    template_data: dict[str, Any]
    vendor: str
    workflow_id: str


@dataclass
class StartFullLevelRecordsWorkflow(Command):
    """Command to start full MARC record processing workflow."""

    collection: str | None
    library: str
    record_type: str
    workflow_id: str


@dataclass
class ParseOrderLevelFiles(Command):
    """Command to parse order-level records from incoming files."""

    collection: str | None
    library: str
    record_type: str
    workflow_id: str
    vendor: str


@dataclass
class MatchOrderLevelRecords(Command):
    """Command to match order-level records after they have been parsed."""

    library: str
    workflow_id: str
    matchpoints: dict[str, str]


@dataclass
class UpdateAndOutputOrderLevelRecords(Command):
    """Command to update and output order-level records."""

    collection: str | None
    library: str
    record_type: str
    template_data: dict[str, Any]
    workflow_id: str


@dataclass
class ParseFullLevelFiles(Command):
    """Command to parse full MARC records from incoming files."""

    collection: str | None
    library: str
    record_type: str
    workflow_id: str


@dataclass
class MatchFullLevelRecords(Command):
    """Command to match full MARC records after they have been parsed."""

    library: str
    workflow_id: str


@dataclass
class UpdateAndOutputFullLevelRecords(Command):
    """Command to update and output full MARC records."""

    collection: str | None
    library: str
    record_type: str
    workflow_id: str
