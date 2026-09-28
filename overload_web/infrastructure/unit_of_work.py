"""Adapter module that defines a unit of work to for use with DB interactions."""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Protocol, runtime_checkable

from sqlmodel import Session

from overload_web.infrastructure import batch_db, file_io, workflow_db

logger = logging.getLogger(__name__)


@runtime_checkable
class AbstractUnitOfWork(Protocol):
    """Protocol defining the Unit of Work for database transactions."""

    batch_repo: batch_db.PVFBatchRepository
    file_repo: file_io.IncomingFileRepository
    job_repo: workflow_db.WorkflowJobRepository

    def __enter__(self) -> AbstractUnitOfWork: ...  # pragma: no branch

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...  # pragma: no branch

    def commit(self) -> None: ...  # pragma: no branch
    def rollback(self) -> None: ...  # pragma: no branch


class SqlModelUnitOfWork(AbstractUnitOfWork):
    def __init__(self, engine):
        self.engine = engine
        self.session = None

    def __enter__(self):
        self.session = Session(self.engine)
        self.batch_repo = batch_db.PVFBatchRepository(session=self.session)
        self.file_repo = file_io.IncomingFileRepository(session=self.session)
        self.job_repo = workflow_db.WorkflowJobRepository(session=self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
