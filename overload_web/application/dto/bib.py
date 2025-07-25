"""This modules contains data transfer objects (DTOs) for the application."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from bookops_marc import Bib

    from overload_web.domain import models


class BibDTO:
    """
    Data Transfer Object for MARC records.

    This class is responsible maintaining a MARC record and its associated
    domain bib.

    Attributes:
        bib: The original MARC record as a `bookops-marc.Bib` object.
        domain_bib: The `DomainBib` object associated with the MARC record.

    """

    def __init__(self, bib: Bib, domain_bib: models.bibs.DomainBib):
        self.bib = bib
        self.domain_bib = domain_bib
