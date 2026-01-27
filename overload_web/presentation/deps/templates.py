"""Dependency injection for the template service."""

import logging
import os
from typing import Annotated, Any, Generator

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from overload_web.application import template_service
from overload_web.order_templates.infrastructure import repository

logger = logging.getLogger(__name__)


def get_postgres_uri() -> str:
    """Get the Postgres database URI from environment variables."""
    db_type = os.environ.get("DB_TYPE", "sqlite")
    user = os.environ.get("POSTGRES_USER")
    pw = os.environ.get("POSTGRES_PASSWORD")
    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT")
    name = os.environ.get("POSTGRES_DB")
    uri = f"{db_type}://{user}:{pw}@{host}:{port}/{name}"
    uri = uri.replace("sqlite://None:None@None:None/None", "sqlite:///:memory:")
    return uri


def get_engine_with_uri():
    return create_engine(get_postgres_uri())


def create_db_and_tables(engine) -> None:
    """Create the database and tables if they do not exist."""
    SQLModel.metadata.create_all(engine)


def get_session(engine) -> Generator[Session, None, None]:
    """Create a new database session."""
    with Session(engine) as session:
        yield session


def template_handler(
    session: Annotated[Any, Depends(get_session)],
) -> Generator[template_service.OrderTemplateService, None, None]:
    """Create an order template service."""
    yield template_service.OrderTemplateService(
        repo=repository.SqlModelRepository(session=session)
    )
