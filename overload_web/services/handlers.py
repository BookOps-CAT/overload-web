from __future__ import annotations

from typing import Any, BinaryIO, Dict, List, Sequence

from overload_web.adapters import marc_adapters
from overload_web.domain import model
from overload_web.services import unit_of_work


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
            bibs.extend(
                [
                    {
                        "library": bib["library"],
                        "orders": [],
                        "bib_id": i["id"],
                        "isbn": i.get("isbn"),
                        "oclc_number": i.get("oclc_number"),
                        "upc": i.get("upc"),
                    }
                    for i in uow.bibs.get_bibs_by_id(value=value, key=key)
                ]
            )
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
            bibs.extend(
                [
                    {
                        "library": bib["library"],
                        "orders": [],
                        "bib_id": i["id"],
                        "isbn": i.get("isbn"),
                        "oclc_number": i.get("oclc_number"),
                        "upc": i.get("upc"),
                    }
                    for i in sierra_bibs
                ]
            )
        domain_bibs = [model.DomainBib(**i) for i in bibs]
        domain_bib.match(bibs=domain_bibs, matchpoints=matchpoints)
        return domain_bib.__dict__


def process_marc_file(
    bib_data: BinaryIO, library: str, uow: unit_of_work.OverloadUnitOfWork
) -> Sequence[model.DomainBib]:
    bibs = []
    reader = marc_adapters.read_marc_file(bib_data, library=library)
    for bib in reader:
        orders = [uow.order_factory.to_domain(i) for i in bib.orders]
        domain_bib = model.DomainBib(
            library=bib.library,
            orders=orders,
            bib_id=bib.sierra_bib_id,
            isbn=bib.isbn,
            oclc_number=list(bib.oclc_nos.values()),
            upc=bib.upc_number,
        )
        bibs.append(domain_bib)
    return bibs
