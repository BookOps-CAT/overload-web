"""Adapter for reading MARC files and converting into domain objects"""

from __future__ import annotations

from typing import BinaryIO, List

from bookops_marc import SierraBibReader

from overload_web.domain import model


def read_marc_file(marc_file: BinaryIO, library: str) -> List[model.DomainBib]:
    """
    Parses a MARC file using `bookops_marc` and converts each `bookops_marc.Bib` object
    record into a `DomainBib` instance.

    Args:
        marc_file: binary stream containing MARC data.
        library: the library to whom the records belong

    Returns:
        list of `DomainBib` instances.
    """
    bibs = []
    reader = SierraBibReader(marc_file, library=library, hide_utf8_warnings=True)
    for record in reader:
        bibs.append(model.DomainBib.from_marc(bib=record))
    return bibs
