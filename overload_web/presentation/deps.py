import logging
import os
from inspect import Parameter, Signature

from fastapi import Form
from pydantic import BaseModel
from sqlmodel import SQLModel, create_engine

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


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def from_form(model_class: BaseModel):
    """
    A generic function used to create an object from an html form.
    HTML forms can only take data as strings so this class method is
    needed in order to parse the data into the correct types.
    """
    form_fields = []
    for field_name, model_field in model_class.model_fields.items():
        annotation = model_field.annotation
        default = Form(...) if model_field.is_required() else Form(default=None)
        form_fields.append((field_name, annotation, default))

    def func(**data):
        return model_class(**data)

    params = [
        Parameter(
            name,
            Parameter.POSITIONAL_OR_KEYWORD,
            default=default,
            annotation=annotation,
        )
        for name, annotation, default in form_fields
    ]
    func.__signature__ = Signature(parameters=params)  # type: ignore[attr-defined]
    return func
