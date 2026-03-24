import logging
from typing import Sequence

from overload_web.application import ports
from overload_web.domain.models import templates

logger = logging.getLogger(__name__)


class CreateOrderTemplate:
    @staticmethod
    def execute(
        repository: ports.SqlRepositoryProtocol, obj: templates.OrderTemplateBase
    ) -> templates.OrderTemplate:
        """
        Save an order template.

        Args:
            repository: a `ports.SqlRepositoryProtocol` object.
            obj: the template data as an `OrderTemplateBase` object.

        Raises:
            ValidationError: If the template lacks a name, agent, or primary_matchpoint.

        Returns:
            The saved template as an `OrderTemplate` object.
        """
        save_template = repository.save(obj=obj)
        return templates.OrderTemplate(**save_template.model_dump())


class GetOrderTemplate:
    @staticmethod
    def execute(
        repository: ports.SqlRepositoryProtocol, template_id: str
    ) -> templates.OrderTemplate | None:
        """
        Retrieve an order template by its ID.

        Args:
            repository: a `ports.SqlRepositoryProtocol` object.
            template_id: unique identifier for the template.

        Returns:
            The retrieved template as a `OrderTemplate` object or None.
        """
        return repository.get(id=template_id)


class ListOrderTemplates:
    @staticmethod
    def execute(
        repository: ports.SqlRepositoryProtocol,
        offset: int | None = 0,
        limit: int | None = 20,
    ) -> Sequence[templates.OrderTemplate]:
        """
        Retrieve a list of templates in the database.

        Args:
            repository: a `ports.SqlRepositoryProtocol` object.
            offset: start position of first `OrderTemplate` object to return.
            limit: the maximum number of `OrderTemplate` objects to return.

        Returns:
            A list of `OrderTemplate` objects.
        """
        return repository.list(offset=offset, limit=limit)


class UpdateOrderTemplate:
    @staticmethod
    def execute(
        repository: ports.SqlRepositoryProtocol,
        template_id: str,
        obj: templates.OrderTemplateBase,
    ) -> templates.OrderTemplate | None:
        """
        Update an existing order template.

        Args:
            repository: a `ports.SqlRepositoryProtocol` object.
            template_id: unique identifier for the template to be updated.
            obj: the data to be replaces as an `OrderTemplateBase` object.

        Returns:
            The updated template as an `OrderTemplate` or None if the template
            does not exist.
        """
        return repository.update(id=template_id, data=obj)
