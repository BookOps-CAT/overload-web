"""Module that tables for process vendor file databases.

Models:
`PVFBatch`
    A pydantic/sqlmodel model that defines a batch containing one or more MARC files
    and their associated processing statistics.

`ProcessedFileModel`
    A pydantic/sqlmodel model that defines a processed MARC file.
`_TemplateModelBase`
    The base data model used to represent an order template and fields that are shared
    by all models within this module.
`TemplateModel`
    The table model that includes all fields within an order template including fields
    that are only required for the template to be saved to the database.
"""

import logging
from typing import Any

from sqlmodel import JSON, Column, Field, Relationship, SQLModel

logger = logging.getLogger(__name__)


class IncomingFileModel(SQLModel, table=True):
    __tablename__ = "incoming_files"
    id: str = Field(default=None, primary_key=True, index=True)
    filename: str = Field(nullable=False)
    workflow_id: str = Field(nullable=False, index=True)
    source: str = Field(nullable=False)
    reference: str = Field(nullable=False)


class PVFBatch(SQLModel, table=True):
    """
    A table model representing a one or more MARC files and their associated
    processing statistics for a single `ProcessOrderLevelRecords`, or
    `ProcessFullRecords` command. This represents the aggregate for the
    process vendor file workflow.
    """

    __tablename__ = "batches"

    id: int = Field(default=None, primary_key=True, index=True)
    files: list["ProcessedFileModel"] = Relationship(
        back_populates="batch", sa_relationship_kwargs={"lazy": "selectin"}
    )
    stats: list[dict[str, Any]] = Field(sa_column=Column(JSON))
    file_names: list[str | None] = Field(sa_column=Column(JSON))
    total_files: int
    total_records: int
    missing_barcodes: list[str | None] | None = Field(sa_column=Column(JSON))
    processing_integrity: bool | None


class ProcessedFileModel(SQLModel, table=True):
    """A table model representing a processed MARC file."""

    __tablename__ = "files"

    id: int | None = Field(default=None, primary_key=True, index=True, exclude=True)
    file_name: str = Field(nullable=False, index=True)
    records: bytes = Field(nullable=False)

    batch_id: int = Field(default=None, foreign_key="batches.id", exclude=True)
    batch: PVFBatch = Relationship(back_populates="files")


class _TemplateModelBase(SQLModel):
    """
    A reusable template for applying consistent values to orders.

    Attributes:
        agent: the user who created the `TemplateModel`
        name: the name to be assigned to the `TemplateModel` in the database

    All other fields correspond to those available in the `Order` domain model.

    """

    acquisition_type: str | None = Field(default=None)
    agent: str = Field(nullable=False, index=True)
    blanket_po: str | None = Field(default=None)
    claim_code: str | None = Field(default=None)
    country: str | None = Field(default=None)
    format: str | None = Field(default=None)
    internal_note: str | None = Field(default=None)
    lang: str | None = Field(default=None)
    material_form: str | None = Field(default=None)
    name: str = Field(nullable=False, unique=True, index=True)
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
    primary_matchpoint: str = Field(nullable=False)
    secondary_matchpoint: str | None = Field(default=None)
    tertiary_matchpoint: str | None = Field(default=None)


class TemplateModel(_TemplateModelBase, table=True):
    """
    A table model representing order templates including all fields required
    for persistence (i.e., all fields present in a `_TemplateModelBase` object
    with the addition of the unique identifier).
    """

    __tablename__ = "templates"
    id: int = Field(default=None, primary_key=True, index=True)
