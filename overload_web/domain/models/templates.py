"""Domain models that define order templates and associated objects."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Optional, Union


@dataclass
class Matchpoints:
    """
    Represents a set of matchpoint values used for identifying duplicate records
    in Sierra.

    Attributes:
        primary: primary field to match on.
        secondary: secondary field to match on.
        tertiary: tertiary field to match on.
    """

    primary: Optional[str] = None
    secondary: Optional[str] = None
    tertiary: Optional[str] = None

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

        All other fields correspond to those available in the `Order` domain model.
    """

    matchpoints: Matchpoints = field(default_factory=Matchpoints)
    agent: Optional[str] = None
    id: Optional[TemplateId] = None
    name: Optional[str] = None

    blanket_po: Optional[str] = None
    copies: Optional[Union[str, int]] = None
    country: Optional[str] = None
    create_date: Optional[Union[datetime.datetime, datetime.date, str]] = None
    format: Optional[str] = None
    fund: Optional[str] = None
    internal_note: Optional[str] = None
    lang: Optional[str] = None
    order_code_1: Optional[str] = None
    order_code_2: Optional[str] = None
    order_code_3: Optional[str] = None
    order_code_4: Optional[str] = None
    order_type: Optional[str] = None
    price: Optional[Union[str, int]] = None
    selector_note: Optional[str] = None
    status: Optional[str] = None
    var_field_isbn: Optional[str] = None
    vendor_code: Optional[str] = None
    vendor_notes: Optional[str] = None
    vendor_title_no: Optional[str] = None


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
