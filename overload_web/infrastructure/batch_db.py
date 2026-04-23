"""Adapter module that defines classes and models related to batches of processed files.

Classes:

`PVFBatchRepository`
    `SQLModel` implementation of `SqlRepositoryProtocol` for managing
    `PVFBatch` objects in a SQL database.

Models:

`PVFBatch`
    A pydantic/sqlmodel model that defines a batch containing one or more MARC files
    and their associated processing statistics.

`PVFReportModel`
    A pydantic/sqlmodel model that defines processing statistics for a process vendor
    file workflow.

`ProcessedFileModel`
    A pydantic/sqlmodel model that defines a processed MARC file.
"""

import logging
from typing import Any

from sqlmodel import JSON, Column, Field, Relationship, Session, SQLModel

logger = logging.getLogger(__name__)


class PVFBatch(SQLModel, table=True):
    """
    A table model representing a one or more MARC files and their associated
    processing statistics for a single `ProcessAcquisitionsRecords`,
    `ProcessCatalogingRecords`, or `ProcessSelectionRecords` command. This
    represents the aggregate for the process vendor file workflow.
    """

    __tablename__ = "batches"

    id: int = Field(default=None, primary_key=True, index=True)
    files: list["ProcessedFileModel"] = Relationship(
        back_populates="batch", sa_relationship_kwargs={"lazy": "selectin"}
    )
    report: "PVFReportModel" = Relationship(
        back_populates="batch", sa_relationship_kwargs={"lazy": "selectin"}
    )


class PVFReportModel(SQLModel, table=True):
    """A table model representing a batch of processing statistics."""

    __tablename__ = "reports"

    id: int = Field(default=None, primary_key=True, index=True, exclude=True)
    action: list[str | None] = Field(sa_column=Column(JSON))
    call_number: list[str | None] = Field(sa_column=Column(JSON))
    call_number_match: list[bool | None] = Field(sa_column=Column(JSON))
    duplicate_records: list[list[str | None]] = Field(sa_column=Column(JSON))
    file_names: list[str | None] = Field(sa_column=Column(JSON))
    mixed: list[list[str | None]] = Field(sa_column=Column(JSON))
    other: list[list[str | None]] = Field(sa_column=Column(JSON))
    resource_id: list[str | None] = Field(sa_column=Column(JSON))
    target_bib_id: list[str | None] = Field(sa_column=Column(JSON))
    target_call_no: list[str | None] = Field(sa_column=Column(JSON))
    target_title: list[str | None] = Field(sa_column=Column(JSON))
    total_files: int
    total_records: int
    updated_by_vendor: list[bool | None] = Field(sa_column=Column(JSON))
    vendor: list[str | None] = Field(sa_column=Column(JSON))
    missing_barcodes: list[str | None] | None = Field(sa_column=Column(JSON))
    processing_integrity: bool | None

    batch_id: int = Field(default=None, foreign_key="batches.id", exclude=True)
    batch: PVFBatch = Relationship(back_populates="report")


class ProcessedFileModel(SQLModel, table=True):
    """A table model representing a processed MARC file."""

    __tablename__ = "files"

    id: int | None = Field(default=None, primary_key=True, index=True, exclude=True)
    file_name: str = Field(nullable=False, index=True)
    records: bytes = Field(nullable=False)

    batch_id: int = Field(default=None, foreign_key="batches.id", exclude=True)
    batch: PVFBatch = Relationship(back_populates="files")


class PVFBatchRepository:
    """
    `SQLModel` repository for `PVFBatch` objects.

    This class is a concrete implementation of the `SqlRepositoryProtocol` protocol.

    Args:
        session: a `sqlmodel.Session`.
    """

    def __init__(self, session: Session):
        self.session = session

    def get(self, id: str | int) -> dict[str, Any] | None:
        """
        Retrieve a `PVFBatch` object by its ID.

        Args:
            id: the primary key of the `PVFBatch`.

        Returns:
            a `PVFBatch` instance as a dictionary or `None` if not found.
        """
        batch = self.session.get(PVFBatch, id)
        if batch:
            return {
                "files": [f.model_dump() for f in batch.files],
                "report": batch.report.model_dump(),
            }
        return None

    def save(self, obj: PVFBatch) -> dict[str, Any]:
        """
        Adds a new `PVFBatch` to the database.

        Args:
            obj: the `PVFBatch` object to save.

        Returns:
            The `PVFBatch` data as a dictionary.
        """
        valid_files = [
            ProcessedFileModel.model_validate(i, from_attributes=True)
            for i in obj.files
        ]
        valid_stats = PVFReportModel(**obj.report)
        valid_batch = PVFBatch(files=valid_files, report=valid_stats)
        self.session.add(valid_batch)
        self.session.commit()
        self.session.refresh(valid_batch)
        return valid_batch.model_dump()
