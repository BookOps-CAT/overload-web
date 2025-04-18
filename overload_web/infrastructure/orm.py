from sqlalchemy import Column, Date, Integer, MetaData, String, Table
from sqlalchemy.orm import composite, registry

from overload_web.domain import model

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
    mapper_registry.map_imperatively(
        model.Template,
        templates,
        properties={
            "matchpoints": composite(
                model.Matchpoints,
                templates.c.primary_matchpoint,
                templates.c.secondary_matchpoint,
                templates.c.tertiary_matchpoint,
            )
        },
    )
