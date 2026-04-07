import logging
from typing import Any

from sqlmodel import JSON, Column, Field, ForeignKey, Relationship, Session, SQLModel

logger = logging.getLogger(__name__)


class PVFBatch(SQLModel, table=True):
    """
    A table model representing a one or more MARC files and their associated
    processing statistics for a single `ProcessOrderRecords` or `ProcessFullRecords`
    command. This represents the aggregate for the process vendor file workflow.
    """

    __tablename__ = "batches"

    id: int = Field(default=None, primary_key=True, index=True)
    action: list[str | None] = Field(sa_column=Column(JSON))
    call_number: list[str | None] = Field(sa_column=Column(JSON))
    call_number_match: list[bool | None] = Field(sa_column=Column(JSON))
    duplicate_records: list[list[str | None]] = Field(sa_column=Column(JSON))
    file_names: list[str | None] = Field(sa_column=Column(JSON))
    files: list["ProcessedMarcFileModel"] = Relationship(
        back_populates="batch", sa_relationship=ForeignKey("files.id")
    )
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
    missing_barcodes: list[str | None] = Field(sa_column=Column(JSON))
    processing_integrity: bool


class ProcessedMarcFileModel(SQLModel):
    file_name: str = Field(nullable=False)
    records: bytes = Field(nullable=False)


class PVFBatchRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, id: str | int) -> dict[str, Any] | None:
        batch = self.session.get(PVFBatch, id)
        return batch.model_dump() if batch else None

    def save(self, obj: PVFBatch) -> dict[str, Any]:
        valid_obj = PVFBatch.model_validate(obj, from_attributes=True)
        self.session.add(valid_obj)
        self.session.commit()
        self.session.refresh(valid_obj)
        return valid_obj.model_dump()
