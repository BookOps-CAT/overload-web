from __future__ import annotations

from typing import Any, BinaryIO, Dict, List, Optional, Sequence

from overload_web.application import unit_of_work
from overload_web.domain import match_service, model
from overload_web.infrastructure import marc_adapters, sierra_adapters


def apply_template_data(
    bib_data: List[Dict[str, Any]], template: Dict[str, Any]
) -> List[Dict[str, Any]]:
    processed_bibs = []
    domain_bibs = [model.DomainBib(**i) for i in bib_data]
    for bib in domain_bibs:
        bib.orders = [
            (model.Order(**i) if isinstance(i, dict) else i) for i in bib.orders
        ]
        bib.apply_template(template_data=template)
        processed_bib = {k: v for k, v in bib.__dict__.items() if k != "orders"}
        processed_bib["orders"] = [i.__dict__ for i in bib.orders]
        processed_bibs.append(processed_bib)
    return processed_bibs


def get_fetcher_for_library(library: str) -> match_service.BibFetcher:
    session: sierra_adapters.SierraSessionProtocol
    if library == "bpl":
        session = sierra_adapters.BPLSolrSession()
    elif library == "nypl":
        session = sierra_adapters.NYPLPlatformSession()
    else:
        raise ValueError("Invalid library. Must be 'bpl' or 'nypl'")
    return sierra_adapters.SierraBibFetcher(session=session, library=library)


def match_bib(
    file_data: BinaryIO,
    library: str,
    matchpoints: List[str],
    fetcher: Optional[match_service.BibFetcher] = None,
) -> List[Dict[str, Any]]:
    if fetcher is None:
        fetcher = get_fetcher_for_library(library=library)
    matcher = match_service.BibMatchService(fetcher=fetcher, matchpoints=matchpoints)

    processed_bibs = []
    bibs = marc_adapters.read_marc_file(marc_file=file_data, library=library)
    for bib in bibs:
        bib.bib_id = matcher.find_best_match(bib)
        processed_bibs.append(bib)
    return [i.__dict__ for i in processed_bibs]


def process_marc_file(bib_data: BinaryIO, library: str) -> Sequence[model.DomainBib]:
    return [i for i in marc_adapters.read_marc_file(bib_data, library=library)]


def save_template(
    data: Dict[str, Any], uow: unit_of_work.UnitOfWorkProtocol
) -> Dict[str, Any]:
    template = model.Template(**data)
    if not template.name or not template.name.strip():
        raise ValueError("Templates must have a name before being saved.")
    if not template.agent or not template.agent.strip():
        raise ValueError("Templates must have an agent before being saved.")
    with uow:
        uow.templates.save(template=template)
        uow.commit()
    return template.__dict__
