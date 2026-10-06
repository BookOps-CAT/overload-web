"""Application service commands for handling operations with order templates."""

import logging
from typing import Sequence

from overload_web.domain.pvf import order_templates, ports

logger = logging.getLogger(__name__)


class SaveNewOrderTemplate:
    @staticmethod
    def execute(
        obj: order_templates.OrderTemplateBase, uow: ports.UnitOfWorkProtocol
    ) -> order_templates.OrderTemplate:
        """
        Save an order template.

        Args:
            obj: the template data as an `OrderTemplateBase` object.
            uow: a `ports.UnitOfWorkProcotol` object.

        Raises:
            ValidationError: If the template lacks a name, agent, or primary_matchpoint.

        Returns:
            The saved template as an `OrderTemplate` domain object.
        """
        with uow:
            save_template = uow.order_templates.save(obj=obj).model_dump()
            uow.commit()
            return order_templates.OrderTemplate(**save_template)


class GetOrderTemplate:
    @staticmethod
    def execute(
        template_id: str, uow: ports.UnitOfWorkProtocol
    ) -> order_templates.OrderTemplate | None:
        """
        Retrieve an order template by its ID.

        Args:
            template_id: unique identifier for the template.
            uow: a `ports.UnitOfWorkProcotol` object.

        Returns:
            The retrieved template as a `OrderTemplate` object or None.
        """
        with uow:
            data = uow.order_templates.get(id=template_id)
            if data:
                return order_templates.OrderTemplate(**data.model_dump())
        return None


class ListOrderTemplates:
    @staticmethod
    def execute(
        uow: ports.UnitOfWorkProtocol, offset: int | None = 0, limit: int | None = 20
    ) -> Sequence[order_templates.OrderTemplate]:
        """
        Retrieve a list of templates in the database.

        Args:
            offset: start position of first `OrderTemplate` object to return.
            limit: the maximum number of `OrderTemplate` objects to return.
            uow: a `ports.UnitOfWorkProcotol` object.
        Returns:
            A list of `OrderTemplate` objects.
        """
        with uow:
            template_list = uow.order_templates.list(offset=offset, limit=limit)
            return [
                order_templates.OrderTemplate(**i.model_dump()) for i in template_list
            ]


class UpdateOrderTemplate:
    @staticmethod
    def execute(
        template_id: str,
        obj: order_templates.OrderTemplateBase,
        uow: ports.UnitOfWorkProtocol,
    ) -> order_templates.OrderTemplate | None:
        """
        Update an existing order template.

        Args:
            obj: the data to be replaces as an `OrderTemplateBase` object.
            template_id: unique identifier for the template to be updated.
            uow: a `ports.UnitOfWorkProcotol` object.
        Returns:
            The updated template as an `OrderTemplate` or None if the template
            does not exist.
        """
        with uow:
            data = uow.order_templates.update(id=template_id, data=obj)
            if data:
                template = data.model_dump()
                uow.commit()
                return order_templates.OrderTemplate(**template)
        return None
