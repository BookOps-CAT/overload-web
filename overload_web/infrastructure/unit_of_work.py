"""Adapter module that defines a unit of work to for use with DB interactions."""

from __future__ import annotations

import logging
from typing import Any, Sequence

from sqlmodel import Session, SQLModel, select

from overload_web.domain.pvf import ports
from overload_web.infrastructure import tables

logger = logging.getLogger(__name__)


class SqlModelUnitOfWork(ports.UnitOfWorkProtocol):
    def __init__(self, engine):
        self.engine = engine
        self.session = None

    def __enter__(self):
        self.session = Session(self.engine)
        self.incoming_files = IncomingFileRepository(session=self.session)
        self.order_templates = OrderTemplateRepository(session=self.session)
        self.processed_batches = PVFBatchRepository(session=self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()


class OrderTemplateRepository(ports.SqlRepositoryProtocol):
    """
    `SQLModel` repository for `TemplateModel` objects.

    This class is a concrete implementation of the `SqlRepositoryProtocol` protocol.

    Args:
        session: a `sqlmodel.Session`.
    """

    def __init__(self, session: Session):
        self.session = session

    def get(self, id: str | int) -> dict[str, Any] | None:
        """
        Retrieve an `OrderTemplate` object by its ID.

        Args:
            id: the primary key of the `OrderTemplate`.

        Returns:
            a `OrderTemplate` instance as a dictionary or `None` if not found.
        """
        template = self.session.get(tables.TemplateModel, id)
        return template.model_dump() if template else None

    def list(
        self, offset: int | None = 0, limit: int | None = 0
    ) -> Sequence[dict[str, Any]]:
        """
        Retrieve all `OrderTemplate` objects in the database.

        Args:
            offset: start position of `OrderTemplate` objects to return
            limit: the maximum number of `OrderTemplate` objects to return

        Returns:
            a sequence of `OrderTemplate` objects.
        """
        statement = select(tables.TemplateModel).offset(offset).limit(limit)
        results = self.session.exec(statement)
        all_templates = results.all()
        return [i.model_dump() for i in all_templates]

    def save(self, obj: tables.TemplateModel) -> dict[str, Any]:
        """
        Adds a new `TemplateModel` to the database.

        Args:
            obj: the `TemplateModel` object to save.

        Returns:
            The `TemplateModel` data as a dictionary.
        """
        valid_obj = tables.TemplateModel.model_validate(obj, from_attributes=True)
        self.session.add(valid_obj)
        self.session.flush()
        self.session.refresh(valid_obj)
        return valid_obj.model_dump()

    def update(self, data: SQLModel, id: str) -> dict[str, Any] | None:
        """
        Updates an existing `OrderTemplate` in the database.

        Args:
            data: the data to be used to update the existing template.
            id: the id of the template to be updated
        Returns:
            a `TemplateModel` instance or `None` if not found.
        """
        template = self.session.get(tables.TemplateModel, id)
        if not template:
            logger.error(f"Template '{id}' does not exist")
        else:
            patch_data = data.model_dump(exclude_unset=True)
            template.sqlmodel_update(patch_data)
            self.session.add(template)
            self.session.flush()
            self.session.refresh(template)
        return template.model_dump() if template else None


class PVFBatchRepository(ports.SqlRepositoryProtocol):
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
        batch = self.session.get(tables.PVFBatch, id)
        if batch:
            return {
                "files": [f.model_dump() for f in batch.files],
                "stats": batch.stats,
                "file_names": batch.file_names,
                "total_files": batch.total_files,
                "total_records": batch.total_records,
                "missing_barcodes": batch.missing_barcodes,
                "processing_integrity": batch.processing_integrity,
            }
        return None

    def save(self, obj: tables.PVFBatch) -> dict[str, Any]:
        """
        Adds a new `PVFBatch` to the database.

        Args:
            obj: the `PVFBatch` object to save.

        Returns:
            The `PVFBatch` data as a dictionary.
        """
        valid_files = [
            tables.ProcessedFileModel.model_validate(i, from_attributes=True)
            for i in obj.files
        ]
        valid_batch = tables.PVFBatch(
            files=valid_files,
            stats=obj.stats,
            file_names=obj.file_names,
            total_files=obj.total_files,
            total_records=obj.total_records,
            missing_barcodes=obj.missing_barcodes,
            processing_integrity=obj.processing_integrity,
        )
        self.session.add(valid_batch)
        self.session.flush()
        self.session.refresh(valid_batch)
        return valid_batch.model_dump()


class IncomingFileRepository(ports.SqlRepositoryProtocol):
    def __init__(self, session: Session):
        self.session = session

    def delete(self, id: str | int) -> None:
        """
        Delete an `IncomingFileModel` object from the workflow's list of files.

        Args:
            id: the ID of the file to delete.

        Returns:
            None
        """
        statement = select(tables.IncomingFileModel).where(
            tables.IncomingFileModel.id == id
        )
        results = self.session.exec(statement)
        file = results.one_or_none()
        self.session.delete(file)

    def list_by_id(self, id: str | int) -> Sequence[dict[str, Any]]:
        """
        Retrieve all `IncomingFileModel` objects in the database.

        Args:
            id: the `workflow_id` whose files to retrieve.

        Returns:
            a sequence of `IncomingFileModel` objects.
        """
        statement = select(tables.IncomingFileModel).where(
            tables.IncomingFileModel.workflow_id == id
        )
        results = self.session.exec(statement)
        all_files = results.all()
        return [i.model_dump() for i in all_files]

    def save(self, obj: tables.IncomingFileModel) -> dict[str, Any]:
        """
        Adds a new `IncomingFileModel` to the database.

        Args:
            obj: the `IncomingFileModel` object to save.

        Returns:
            The `IncomingFileModel` data as a dictionary.
        """
        valid_obj = tables.IncomingFileModel.model_validate(obj, from_attributes=True)
        self.session.add(valid_obj)
        self.session.flush()
        self.session.refresh(valid_obj)
        return valid_obj.model_dump()
