from __future__ import annotations

from typing import Any, BinaryIO, Dict, List, Sequence

from overload_web.application import unit_of_work
from overload_web.domain import model
from overload_web.infrastructure import marc_adapters


def get_bibs_by_key(
    bib: Dict[str, Any],
    matchpoints: List[str],
    uow: unit_of_work.OverloadUnitOfWork,
) -> List[Dict[str, Any]]:
    with uow:
        bibs = []
        for key in matchpoints:
            value = bib.get(key)
            if not value:
                continue
            bibs.extend([i for i in uow.bibs.get_bibs_by_id(value=value, key=key)])
        return bibs


def match_bib(
    bib: Dict[str, Any],
    matchpoints: List[str],
    uow: unit_of_work.OverloadUnitOfWork,
) -> Dict[str, Any]:
    domain_bib = model.DomainBib(**bib)
    with uow:
        bibs = []
        for key in matchpoints:
            value = bib.get(key)
            if not value:
                continue
            sierra_bibs = uow.bibs.get_bibs_by_id(value=value, key=key)
            for bib in sierra_bibs:
                bib.update({"library": domain_bib.library, "orders": []})
            bibs.extend(sierra_bibs)
        domain_bibs = [model.DomainBib(**i) for i in bibs]
        domain_bib.match(bibs=domain_bibs, matchpoints=matchpoints)
        return domain_bib.__dict__


def process_marc_file(bib_data: BinaryIO, library: str) -> Sequence[model.DomainBib]:
    return [i for i in marc_adapters.read_marc_file(bib_data, library=library)]
