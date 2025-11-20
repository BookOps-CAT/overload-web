import logging
import os
from typing import Annotated, Any, Generator

from fastapi import Depends
from sqlmodel import Session, create_engine

from overload_web.application import template_service
from overload_web.order_templates.infrastructure import repository

logger = logging.getLogger(__name__)


def get_session() -> Generator[Session, None, None]:
    uri = f"{os.environ.get('DB_TYPE', 'sqlite')}://{os.environ.get('POSTGRES_USER')}:{os.environ.get('POSTGRES_PASSWORD')}@{os.environ.get('POSTGRES_HOST')}:{os.environ.get('POSTGRES_PORT')}/{os.environ.get('POSTGRES_DB')}"
    uri.replace("sqlite://None:None@None:None/None", "sqlite:///:memory:")
    engine = create_engine(uri)
    with Session(engine) as session:
        yield session


def template_handler(
    session: Annotated[Any, Depends(get_session)],
) -> Generator[template_service.OrderTemplateService, None, None]:
    yield template_service.OrderTemplateService(
        repo=repository.SqlModelRepository(session=session)
    )
