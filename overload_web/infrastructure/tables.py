"""Tables and data models for databases used within the process vendor file workflow.

Models:

`IncomingFileModel`
    A pydantic/sqlmodel table model that defines a file that has been uploaded
     o a workflow and will be processed as part of that workflow.

`ProcessedFileModel`
    A pydantic/sqlmodel table model that defines a processed MARC file.

`PVFBatch`
    A pydantic/sqlmodel table model that defines a batch containing one or more MARC
    files and their associated processing statistics.

`TemplateUpdateModel`
    The pydantic/sqlmodel model used to represent an order template during updates
    to that order template's record in a database.

`TemplateModel`
    The pydantic/sqlmodel table model that includes all fields within an order
    template including fields that are only required for the template to be saved
    to the database.

`WorkflowUpdateModel`
    The pydantic/sqlmodel model used to represent a workflow during updates to the
    workflow's record in a database.

`WorkflowStateModel`
    The pydantic/sqlmodel table model that includes all fields within workflow records
    including fields that are only required for the workflow to be saved to the database
    and links to the workflow's associated `IncomingFileModel` objects.
"""

import logging
from typing import Any

from sqlmodel import JSON, Column, Field, Relationship, SQLModel

logger = logging.getLogger(__name__)


class IncomingFileModel(SQLModel, table=True):
    """A table model representing a file that has been uploaded to a workflow."""

    __tablename__ = "incoming_files"
    id: str = Field(default=None, primary_key=True, index=True)
    filename: str = Field(nullable=False)
    reference: str = Field(nullable=False)
    source: str = Field(nullable=False)
    workflow_id: str = Field(nullable=False, index=True, foreign_key="workflows.id")

    workflow: "WorkflowStateModel" = Relationship(back_populates="files")


class ProcessedFileModel(SQLModel, table=True):
    """A table model representing a processed MARC file."""

    __tablename__ = "files"

    id: int | None = Field(default=None, primary_key=True, index=True, exclude=True)
    batch_id: int = Field(default=None, foreign_key="batches.id", exclude=True)
    file_name: str = Field(nullable=False, index=True)
    records: bytes = Field(nullable=False)

    batch: "PVFBatch" = Relationship(back_populates="files")


class PVFBatch(SQLModel, table=True):
    """A table model representing MARC files and their associated processing stats."""

    __tablename__ = "batches"

    id: int = Field(default=None, primary_key=True, index=True)
    file_names: list[str | None] = Field(sa_column=Column(JSON))
    missing_barcodes: list[str | None] | None = Field(sa_column=Column(JSON))
    processing_integrity: bool | None
    stats: list[dict[str, Any]] = Field(sa_column=Column(JSON))
    total_files: int
    total_records: int

    files: list["ProcessedFileModel"] = Relationship(
        back_populates="batch", sa_relationship_kwargs={"lazy": "selectin"}
    )


class TemplateUpdateModel(SQLModel):
    """A model representing updates to be made to a `TemplateModel`.

    Attributes:
        agent: the user who created the `TemplateModel`

    All other fields correspond to those available in the `OrderTemplate` domain model.

    """

    acquisition_type: str | None = Field(default=None)
    agent: str | None = Field(default=None)
    blanket_po: str | None = Field(default=None)
    claim_code: str | None = Field(default=None)
    country: str | None = Field(default=None)
    format: str | None = Field(default=None)
    internal_note: str | None = Field(default=None)
    lang: str | None = Field(default=None)
    material_form: str | None = Field(default=None)
    name: str | None = Field(default=None)
    order_code_1: str | None = Field(default=None)
    order_code_2: str | None = Field(default=None)
    order_code_3: str | None = Field(default=None)
    order_code_4: str | None = Field(default=None)
    order_note: str | None = Field(default=None)
    order_type: str | None = Field(default=None)
    receive_action: str | None = Field(default=None)
    selector_note: str | None = Field(default=None)
    vendor_code: str | None = Field(default=None)
    vendor_notes: str | None = Field(default=None)
    vendor_title_no: str | None = Field(default=None)
    primary_matchpoint: str | None = Field(default=None)
    secondary_matchpoint: str | None = Field(default=None)
    tertiary_matchpoint: str | None = Field(default=None)


class TemplateModel(TemplateUpdateModel, table=True):
    """A reusable template for applying consistent values to orders.

    This table model represents order templates including all fields required
    for persistence (i.e., all fields present in a `TemplateUpdateModel` object
    with the addition of the unique identifier, and required agent, name, and
    primary_matchpoint values).
    """

    __tablename__ = "templates"
    id: int = Field(default=None, primary_key=True, index=True)
    agent: str = Field(nullable=False, index=True)
    name: str = Field(nullable=False, unique=True, index=True)
    primary_matchpoint: str = Field(nullable=False)


class WorkflowUpdateModel(SQLModel):
    """A model representing updates to be made to a `WorkflowStateModel`."""

    batch_id: int | None = Field(default=None)
    collection: str | None = Field(default=None)
    error_message: str | None = Field(default=None)
    library: str | None = Field(default=None)
    matchpoints: dict[str, str] | None = Field(default=None, sa_type=JSON)
    record_type: str | None = Field(default=None)
    status: str = Field(nullable=False, index=True)
    template_data: dict[str, Any] | None = Field(default=None, sa_type=JSON)


class WorkflowStateModel(WorkflowUpdateModel, table=True):
    """Tracks the state of a long-running process."""

    __tablename__ = "workflows"
    id: str = Field(primary_key=True, index=True)

    files: list["IncomingFileModel"] = Relationship(
        back_populates="workflow", sa_relationship_kwargs={"lazy": "selectin"}
    )
