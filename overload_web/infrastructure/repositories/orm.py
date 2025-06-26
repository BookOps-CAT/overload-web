"""
SQLAlchemy ORM setup for mapping domain models to relational database tables.

Defines:
- `templates`: Table schema for `Template` entities.
- `start_mappers()`: Binds `Template` domain model to the `templates` table using SQLAlchemy's `composite` for matchpoints.
"""

from __future__ import annotations

import logging

from sqlalchemy import Column, Date, Integer, MetaData, String, Table
from sqlalchemy.orm import composite, registry

from overload_web.domain import models

logger = logging.getLogger(__name__)
metadata = MetaData()
mapper_registry = registry(metadata=metadata)

templates = Table(
    "templates",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String, nullable=False, unique=True),
    Column("agent", String, nullable=False),
    Column("audience", String),
    Column("blanket_po", String),
    Column("copies", String),
    Column("country", String),
    Column("create_date", Date),
    Column("format", String),
    Column("fund", String),
    Column("internal_note", String),
    Column("lang", String),
    Column("order_type", String),
    Column("price", String),
    Column("selector", String),
    Column("selector_note", String),
    Column("source", String),
    Column("status", String),
    Column("var_field_isbn", String),
    Column("vendor_code", String),
    Column("vendor_notes", String),
    Column("vendor_title_no", String),
    Column("primary_matchpoint", String),
    Column("secondary_matchpoint", String),
    Column("tertiary_matchpoint", String),
)


def start_mappers() -> None:
    """
    Configures ORM mappings between domain models and relational schema using
    `SQLAlchemy`.

    Maps the `Template` model to the `templates` table and configures composite fields.
    """
    mapper_registry.map_imperatively(
        models.templates.Template,
        templates,
        properties={
            "matchpoints": composite(
                models.templates.Matchpoints,
                templates.c.primary_matchpoint,
                templates.c.secondary_matchpoint,
                templates.c.tertiary_matchpoint,
            )
        },
    )
