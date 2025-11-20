import logging
import os
from inspect import Parameter, Signature

from fastapi import Form
from pydantic import BaseModel
from sqlmodel import SQLModel, create_engine

from overload_web.shared import schemas

logger = logging.getLogger(__name__)


class MatchpointSchema(BaseModel, schemas._Matchpoints):
    """Pydantic model for serializing/deserializing matchpoints from order templates"""


def create_db_and_tables():
    uri = f"{os.environ.get('DB_TYPE', 'sqlite')}://{os.environ.get('POSTGRES_USER')}:{os.environ.get('POSTGRES_PASSWORD')}@{os.environ.get('POSTGRES_HOST')}:{os.environ.get('POSTGRES_PORT')}/{os.environ.get('POSTGRES_DB')}"
    uri.replace("sqlite://None:None@None:None/None", "sqlite:///:memory:")
    engine = create_engine(uri)
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
