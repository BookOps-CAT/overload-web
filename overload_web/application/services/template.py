"""
Unit of work pattern for coordinating template-related database operations.

Defines a protocol and concrete implementation that manages the lifecycle of a
`SQLAlchemy` session and encapsulates transaction boundaries.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from overload_web.domain import models, protocols

logger = logging.getLogger(__name__)


class TemplateService:
    def __init__(self, uow: protocols.repositories.UnitOfWorkProtocol) -> None:
        self.uow = uow

    def get_template(self, template_id: str) -> Optional[models.templates.Template]:
        with self.uow:
            return self.uow.templates.get(id=template_id)

    def save_template(self, data: dict[str, Any]) -> dict[str, Any]:
        template = models.templates.Template(**data)

        if not template.name or not template.name.strip():
            raise ValueError("Templates must have a name before being saved.")
        if not template.agent or not template.agent.strip():
            raise ValueError("Templates must have an agent before being saved.")

        with self.uow:
            self.uow.templates.save(obj=template)
            self.uow.commit()

        return template.__dict__
