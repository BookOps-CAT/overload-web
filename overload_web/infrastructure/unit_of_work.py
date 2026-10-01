"""Adapter module that defines a unit of work to for use with DB interactions."""

from __future__ import annotations

import logging

from sqlmodel import Session

from overload_web.infrastructure import batch_db, file_io, template_db

logger = logging.getLogger(__name__)


class SqlModelUnitOfWork:
    def __init__(self, engine):
        self.engine = engine
        self.session = None

    def __enter__(self):
        self.session = Session(self.engine)
        self.incoming_files = file_io.IncomingFileRepository(session=self.session)
        self.order_templates = template_db.OrderTemplateRepository(session=self.session)
        self.processed_batches = batch_db.PVFBatchRepository(session=self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
