import logging
from typing import Any

from pydantic import model_serializer
from sqlmodel import JSON, Column, Field, Relationship, Session, SQLModel

logger = logging.getLogger(__name__)


class PVFBatch(SQLModel, table=True):
    """
    A table model representing a one or more MARC files and their associated
    processing statistics for a single `ProcessOrderRecords` or `ProcessFullRecords`
    command. This represents the aggregate for the process vendor file workflow.
    """

    __tablename__ = "batches"

    id: int = Field(default=None, primary_key=True, index=True)
    files: list["ProcessedFileModel"] = Relationship(
        back_populates="batch", sa_relationship_kwargs={"lazy": "selectin"}
    )
    report: "PVFReportModel" = Relationship(
        back_populates="batch", sa_relationship_kwargs={"lazy": "selectin"}
    )

    @model_serializer
    def dump_model(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "files": [f.model_dump() for f in self.files],
            "report": self.report.model_dump(),
        }


class PVFReportModel(SQLModel, table=True):
    __tablename__ = "reports"

    id: int = Field(default=None, primary_key=True, index=True)
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

    batch_id: int = Field(default=None, foreign_key="batches.id")
    batch: PVFBatch = Relationship(back_populates="report")

    @model_serializer
    def dump_model(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "call_number": self.call_number,
            "call_number_match": self.call_number_match,
            "duplicate_records": self.duplicate_records,
            "file_names": self.file_names,
            "mixed": self.mixed,
            "other": self.other,
            "resource_id": self.resource_id,
            "target_bib_id": self.target_bib_id,
            "target_call_no": self.target_call_no,
            "target_title": self.target_title,
            "total_files": self.total_files,
            "total_records": self.total_records,
            "updated_by_vendor": self.updated_by_vendor,
            "vendor": self.vendor,
            "missing_barcodes": self.missing_barcodes,
            "processing_integrity": self.processing_integrity,
        }


class ProcessedFileModel(SQLModel, table=True):
    __tablename__ = "files"

    id: int | None = Field(default=None, primary_key=True, index=True)
    file_name: str = Field(nullable=False, index=True)
    records: bytes = Field(nullable=False)

    batch_id: int = Field(default=None, foreign_key="batches.id")
    batch: PVFBatch = Relationship(back_populates="files")

    @model_serializer
    def dump_model(self) -> dict[str, Any]:
        return {"file_name": self.file_name, "records": self.records}


class PVFBatchRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, id: str | int) -> dict[str, Any] | None:
        batch = self.session.get(PVFBatch, id)
        return batch.model_dump() if batch else None

    def save(self, obj: PVFBatch) -> dict[str, Any]:
        valid_files = [
            ProcessedFileModel.model_validate(i, from_attributes=True)
            for i in obj.files
        ]
        valid_stats = PVFReportModel.model_validate(obj.report, from_attributes=True)
        valid_batch = PVFBatch(files=valid_files, report=valid_stats)
        self.session.add(valid_batch)
        self.session.commit()
        self.session.refresh(valid_batch)
        return valid_batch.model_dump()
