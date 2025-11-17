"""This modules contains data transfer objects (DTOs) for the application.

The data transfer objects defined within this module allow a domain object
to be bound with associated objects that are reliant on external dependencies.
"""

from __future__ import annotations

from bookops_marc import Bib

from overload_web.bib_records.domain import bibs


class BibDTO:
    """
    Data Transfer Object for MARC records.

    This class is responsible binding a MARC record and its associated
    domain bib.

    Attributes:
        bib: The original MARC record as a `bookops_marc.Bib` object.
        domain_bib: The `DomainBib` object associated with the MARC record.
        vendor_info: The `VendorInfo` object associated with the MARC record.

    """

    def __init__(
        self,
        bib: Bib,
        domain_bib: bibs.DomainBib,
        vendor_info: bibs.VendorInfo,
    ):
        self.bib = bib
        self.domain_bib = domain_bib
        self.vendor_info = vendor_info
