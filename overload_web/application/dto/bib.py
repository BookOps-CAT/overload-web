"""This modules contains data transfer objects (DTOs) for the application."""

from bookops_marc import Bib

from overload_web.domain.models import bibs


class BibDTO:
    """
    Data Transfer Object for MARC records.

    This class is responsible maintaining a MARC record and its associated
    domain bib.

    Attributes:
        bib: The original MARC record as a `bookops-marc.Bib` object.
        domain_bib: The `DomainBib` object associated with the MARC record.

    """

    def __init__(self, bib: Bib, domain_bib: bibs.DomainBib):
        self.bib = bib
        self.domain_bib = domain_bib
