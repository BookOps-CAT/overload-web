from __future__ import annotations

from typing import BinaryIO, List

from bookops_marc import SierraBibReader

from overload_web.domain import model


def read_marc_file(marc_file: BinaryIO, library: str) -> List[model.DomainBib]:
    bibs = []
    reader = SierraBibReader(marc_file, library=library, hide_utf8_warnings=True)
    for record in reader:
        bibs.append(model.DomainBib.from_marc(bib=record))
    return bibs
