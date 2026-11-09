"""Commands used in vendor processing workflows."""

from dataclasses import dataclass
from typing import Any

from overload_web.domain.pvf import order_templates
from overload_web.domain.shared import Command


@dataclass
class InitializeWorkflow(Command):
    """Command to create a new workflow."""

    workflow_id: str


@dataclass
class StartOrderLevelRecordsWorkflow(Command):
    """Command to start an order-level processing workflow."""

    collection: str | None
    library: str
    matchpoints: dict[str, str]
    record_type: str
    template_data: dict[str, Any]
    vendor: str
    workflow_id: str


@dataclass
class StartFullLevelRecordsWorkflow(Command):
    """Command to start a full MARC record processing workflow."""

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
class ParseFullLevelFiles(Command):
    """Command to parse full MARC records from incoming files."""

    collection: str | None
    library: str
    record_type: str
    workflow_id: str


@dataclass
class MatchOrderLevelRecords(Command):
    """Command to match order-level records after they have been parsed."""

    library: str
    workflow_id: str
    matchpoints: dict[str, str]


@dataclass
class MatchFullLevelRecords(Command):
    """Command to match full MARC records after they have been parsed."""

    library: str
    workflow_id: str


@dataclass
class UpdateAndOutputOrderLevelRecords(Command):
    """Command to update and output order-level records."""

    collection: str | None
    library: str
    record_type: str
    template_data: dict[str, Any]
    workflow_id: str


@dataclass
class UpdateAndOutputFullLevelRecords(Command):
    """Command to update and output full MARC records."""

    collection: str | None
    library: str
    record_type: str
    workflow_id: str


@dataclass(frozen=True)
class UploadFileToWorkflow(Command):
    """Command to add an incoming file to a workflow."""

    workflow_id: str
    filename: str
    content: bytes
    source: str


@dataclass(frozen=True)
class DeleteFileFromWorkflow(Command):
    """Command to remove a file from a workflow."""

    workflow_id: str
    file_id: str


@dataclass(frozen=True)
class CreateOrderTemplate(Command):
    """Command to save a new order template to the database."""

    data: order_templates.OrderTemplateBase


@dataclass(frozen=True)
class UpdateOrderTemplate(Command):
    """Command to update an existing order template within the database."""

    template_id: str
    data: order_templates.OrderTemplateBase


@dataclass(frozen=True)
class CreateOutputReport(Command):
    """Command a report summary for a batch of processed records."""

    batch_id: str
    record_type: str
