"""This modules contains data transfer objects (DTOs) for the application."""

import copy
import datetime
from typing import Any, Dict, List

from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.domain import model


class BibDTO:
    """
    Data Transfer Object for MARC records.

    This class is responsible maintaining a MARC record and its associated
    domain bib.

    Attributes:
        bib: The original MARC record as a `bookops-marc.Bib` object.
        domain_bib: The `DomainBib` object associated with the MARC record.

    """

    def __init__(self, bib: Bib, domain_bib: model.DomainBib):
        self.bib = bib
        self.domain_bib = domain_bib

    def _update_order_fields(self, record: Bib) -> None:
        record.remove_fields("960", "961")
        for order in self.domain_bib.orders:
            order_data = order._marc_mapping()
            for tag in ["960", "961"]:
                subfields = []
                for k, v in order_data[tag].items():
                    if v is None:
                        continue
                    elif isinstance(v, list):
                        subfields.extend([Subfield(code=k, value=str(i)) for i in v])
                    elif isinstance(v, (datetime.date, datetime.datetime)):
                        date = datetime.datetime.strftime(v, format="%Y-%m-%d")
                        subfields.append(Subfield(code=k, value=date))
                    else:
                        subfields.append(Subfield(code=k, value=str(v)))
                record.add_field(
                    Field(tag=tag, indicators=Indicators(" ", " "), subfields=subfields)
                )
        self.bib = record

    def _update_bib_id(self, record: Bib) -> None:
        if self.domain_bib.bib_id:
            record.remove_fields("907")
            record.add_ordered_field(
                Field(
                    tag="907",
                    indicators=Indicators(" ", " "),
                    subfields=[
                        Subfield(
                            code="a", value=f".b{self.domain_bib.bib_id.strip('.b')}"
                        )
                    ],
                )
            )
            self.bib = record

    def update_bib_fields(self, fields: List[Dict[str, Any]] = []) -> None:
        record = copy.deepcopy(self.bib)
        self._update_bib_id(record)
        for field in fields:
            if field and not field.get(field["tag"]):
                record.add_ordered_field(
                    Field(
                        tag=field["tag"],
                        indicators=Indicators(field["ind1"], field["ind2"]),
                        subfields=[
                            Subfield(code=field["subfield_code"], value=field["value"])
                        ],
                    )
                )
        self.bib = record

    def update_order_fields(self) -> None:
        record = copy.deepcopy(self.bib)
        self._update_order_fields(record)
