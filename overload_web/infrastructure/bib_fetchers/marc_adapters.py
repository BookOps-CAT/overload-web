"""Adapter for reading MARC files and converting into domain objects"""

from __future__ import annotations

from typing import BinaryIO, List

from bookops_marc import SierraBibReader

from overload_web.application import dto
from overload_web.domain import models


def read_marc_file(marc_file: BinaryIO, library: str) -> List[dto.bib.BibDTO]:
    """
    Parses a MARC file using `bookops_marc` returns a list of data transfer
    objects containing the MARC record and its associated domain bib.

    Args:
        marc_file: binary stream containing MARC data.
        library: the library to whom the records belong

    Returns:
        list of `BibDTO` objects.
    """
    bibs = []
    reader = SierraBibReader(marc_file, library=library, hide_utf8_warnings=True)
    for record in reader:
        obj = dto.bib.BibDTO(
            bib=record, domain_bib=models.bibs.DomainBib.from_marc(record)
        )
        bibs.append(obj)
    return bibs
