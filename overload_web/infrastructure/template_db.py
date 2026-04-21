"""Adapter module that defines a relational database and associated tables for
order template (`TemplateModel`) objects.

Classes:

`OrderTemplateRepository`
    `SQLModel` implementation of `SqlRepositoryProtocol` for managing
    `TemplateModel` objects in a SQL database.

Models:

`_TemplateModelBase`
    The base data model used to represent an order template and fields that are shared
    by all models within this module.
`TemplateModel`
    The table model that includes all fields within an order template including fields
    that are only required for the template to be saved to the database.
"""

import logging
from typing import Any, Sequence

from sqlmodel import Field, Session, SQLModel, select

logger = logging.getLogger(__name__)


class _TemplateModelBase(SQLModel):
    """
    A reusable template for applying consistent values to orders.

    Attributes:
        name: the name to be associated with the `TemplateModel` in the database
        agent: the user who created the `TemplateModel`

    All other fields correspond to those available in the `Order` domain model.

    """

    acquisition_type: str | None = Field(default=None)
    agent: str = Field(nullable=False, index=True)
    blanket_po: str | None = Field(default=None)
    claim_code: str | None = Field(default=None)
    country: str | None = Field(default=None)
    format: str | None = Field(default=None)
    internal_note: str | None = Field(default=None)
    lang: str | None = Field(default=None)
    material_form: str | None = Field(default=None)
    name: str = Field(nullable=False, unique=True, index=True)
    order_code_1: str | None = Field(default=None)
    order_code_2: str | None = Field(default=None)
    order_code_3: str | None = Field(default=None)
    order_code_4: str | None = Field(default=None)
    order_note: str | None = Field(default=None)
    order_type: str | None = Field(default=None)
    receive_action: str | None = Field(default=None)
    selector_note: str | None = Field(default=None)
    vendor_code: str | None = Field(default=None)
    vendor_notes: str | None = Field(default=None)
    vendor_title_no: str | None = Field(default=None)
    primary_matchpoint: str = Field(nullable=False)
    secondary_matchpoint: str | None = Field(default=None)
    tertiary_matchpoint: str | None = Field(default=None)


class TemplateModel(_TemplateModelBase, table=True):
    """
    A table model representing order templates including all fields required
    for persistence (i.e., all fields present in a `_TemplateModelBase` object
    with the addition of the unique identifier).
    """

    __tablename__ = "templates"
    id: int = Field(default=None, primary_key=True, index=True)


class OrderTemplateRepository:
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
        Retrieve a `OrderTemplate` object by its ID.

        Args:
            id: the primary key of the `OrderTemplate`.

        Returns:
            a `OrderTemplate` instance as a dictionary or `None` if not found.
        """
        template = self.session.get(TemplateModel, id)
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
        statement = select(TemplateModel).offset(offset).limit(limit)
        results = self.session.exec(statement)
        all_templates = results.all()
        return [i.model_dump() for i in all_templates]

    def save(self, obj: TemplateModel) -> dict[str, Any]:
        """
        Adds a new `TemplateModel` to the database.

        Args:
            obj: the `TemplateModel` object to save.

        Returns:
            The `TemplateModel` data as a dictionary.
        """
        valid_obj = TemplateModel.model_validate(obj, from_attributes=True)
        self.session.add(valid_obj)
        self.session.commit()
        self.session.refresh(valid_obj)
        return valid_obj.model_dump()

    def update(self, id: str, data: SQLModel) -> dict[str, Any] | None:
        """
        Updates an existing `OrderTemplate` in the database.

        Args:
            id: the id of the template to be updated
            data: the data to be used to update the existing template.
        Returns:
            a `TemplateModel` instance or `None` if not found.
        """
        template = self.session.get(TemplateModel, id)
        if not template:
            logger.error(f"Template '{id}' does not exist")
        else:
            patch_data = data.model_dump(exclude_unset=True)
            template.sqlmodel_update(patch_data)
            self.session.add(template)
            self.session.commit()
            self.session.refresh(template)
        return template.model_dump() if template else None
