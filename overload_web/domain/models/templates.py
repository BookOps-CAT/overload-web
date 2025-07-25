"""Domain models that define order templates and associated objects."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field


@dataclass
class Matchpoints:
    """
    Represents a set of matchpoint values used for identifying duplicate records
    in Sierra. When matching records against Sierra, each matchpoint is used in
    order until a match is found.

    Attributes:
        primary: primary field to match on.
        secondary: secondary field to match on.
        tertiary: tertiary field to match on.
    """

    primary: str | None = None
    secondary: str | None = None
    tertiary: str | None = None

    def __init__(self, *args, **kwargs):
        """
        Initialize `Matchpoints` from positional or keyword arguments.

        Raises:
            ValueError: If tertiary matchpoint is provided without a secondary.
        """
        if "tertiary" in kwargs and "secondary" not in kwargs and len(args) < 2:
            raise ValueError("Cannot have tertiary matchpoint without secondary.")
        elif len(args) + len(kwargs) > 3:
            raise ValueError("Matchpoints should be passed no more than three values.")

        keys = ["primary", "secondary", "tertiary"]
        values = list(args)

        for key in keys:
            if key in kwargs and len(values) < keys.index(key) + 1:
                values.append(kwargs[key])

        while len(values) < 3:
            values.append(None)

        self.primary, self.secondary, self.tertiary = values[:3]

    def as_list(self) -> list[str]:
        """Return the matchpoints as a list"""
        return [i for i in (self.primary, self.secondary, self.tertiary) if i]

    def __composite_values__(self):
        return self.primary, self.secondary, self.tertiary

    def __eq__(self, other) -> bool:
        if not isinstance(other, Matchpoints):
            return NotImplemented
        return self.__composite_values__() == other.__composite_values__()

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


@dataclass(kw_only=True)
class Template:
    """
    A reusable template for applying consistent values to orders.

    Attributes:
        matchpoints: a `Matchpoints` object used to identify matched bibs in Sierra.
        agent: the user who created the template.
        id: a unique idenfier for the template
        name: a human-readable name for the template

        All other fields correspond to those available in the `Order` domain model.
    """

    matchpoints: Matchpoints = field(default_factory=Matchpoints)
    agent: str | None = None
    id: TemplateId | None = None
    name: str | None = None

    blanket_po: str | None = None
    copies: str | int | None = None
    country: str | None = None
    create_date: datetime.datetime | datetime.date | str | None = None
    format: str | None = None
    fund: str | None = None
    internal_note: str | None = None
    lang: str | None = None
    order_code_1: str | None = None
    order_code_2: str | None = None
    order_code_3: str | None = None
    order_code_4: str | None = None
    order_type: str | None = None
    price: str | int | None = None
    selector_note: str | None = None
    status: str | None = None
    var_field_isbn: str | None = None
    vendor_code: str | None = None
    vendor_notes: str | None = None
    vendor_title_no: str | None = None


@dataclass(frozen=True)
class TemplateId:
    """A dataclass to define a TemplateId as an entity"""

    value: str

    def __post_init__(self):
        """Validate that the template ID is a string"""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("TemplateId must be a non-empty string.")

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"TemplateId(value={self.value!r})"
