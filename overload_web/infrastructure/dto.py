"""This modules contains data transfer objects (DTOs) for the application.

The data transfer objects defined within this module allow a domain object
to be bound with associated objects that are reliant on external dependencies.
"""

from __future__ import annotations

import copy
from typing import Optional

from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.domain import models


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
        domain_bib: models.bibs.DomainBib,
        vendor_info: models.bibs.VendorInfo,
    ):
        self.bib = bib
        self.domain_bib = domain_bib
        self.vendor_info = vendor_info

    def update(self, bib_id: Optional[models.bibs.BibId]) -> None:
        """
        Update the bib_id associated with a `BibDTO.bib` object to reflect a change made
        to its corresponding `DomainBib` object.
        """
        if bib_id:
            # first normalize the bib_id
            normalized_bib_id = f".b{str(bib_id).strip('.b')}"

            # then update the domain bib
            self.domain_bib.bib_id = models.bibs.BibId(normalized_bib_id)

            # finally update the MARC record
            bib_rec = copy.deepcopy(self.bib)
            bib_rec.remove_fields("907")
            bib_rec.add_ordered_field(
                Field(
                    tag="907",
                    indicators=Indicators(" ", " "),
                    subfields=[Subfield(code="a", value=normalized_bib_id)],
                )
            )
            self.bib = bib_rec
