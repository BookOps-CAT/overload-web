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

from overload_web.domain.pvf import reporting

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
    processing_statistics: list[dict[str, Any]] = Field(sa_column=Column(JSON))
    file_names: list[str | None] = Field(sa_column=Column(JSON))
    total_files: int
    total_records: int
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
            report = batch.report
            return {
                "files": [f.model_dump() for f in batch.files],
                "report": {
                    "processing_statistics": report.processing_statistics,
                    "file_names": report.file_names,
                    "total_files": report.total_files,
                    "total_records": report.total_records,
                    "missing_barcodes": report.missing_barcodes,
                    "processing_integrity": report.processing_integrity,
                },
            }
        return None

    def save(self, obj: reporting.ProcessedFileBatch) -> dict[str, Any]:
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
        valid_stats = PVFReportModel(
            processing_statistics=obj.report.records,
            file_names=obj.report.file_names,
            total_files=obj.report.total_files,
            total_records=obj.report.total_records,
            missing_barcodes=obj.report.missing_barcodes,
            processing_integrity=obj.report.processing_integrity,
        )
        valid_batch = PVFBatch(files=valid_files, report=valid_stats)
        self.session.add(valid_batch)
        self.session.commit()
        self.session.refresh(valid_batch)
        return valid_batch.model_dump()
