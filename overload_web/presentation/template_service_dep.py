import logging
import os
from typing import Annotated, Any, Generator

from fastapi import Depends
from sqlmodel import Session, create_engine

from overload_web.application import template_service
from overload_web.order_templates.infrastructure import repository

logger = logging.getLogger(__name__)


def get_postgres_uri() -> str:
    db_type = os.environ.get("DB_TYPE", "sqlite")
    user = os.environ.get("POSTGRES_USER")
    pw = os.environ.get("POSTGRES_PASSWORD")
    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT")
    name = os.environ.get("POSTGRES_DB")
    uri = f"{db_type}://{user}:{pw}@{host}:{port}/{name}"
    uri = uri.replace("sqlite://None:None@None:None/None", "sqlite:///:memory:")
    return uri


engine = create_engine(get_postgres_uri())


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def template_handler(
    session: Annotated[Any, Depends(get_session)],
) -> Generator[template_service.OrderTemplateService, None, None]:
    yield template_service.OrderTemplateService(
        repo=repository.SqlModelRepository(session=session)
    )
