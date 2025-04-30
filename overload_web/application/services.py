from __future__ import annotations

from typing import Any, BinaryIO, Dict, List, Optional, Sequence

from overload_web.domain import match_service, model
from overload_web.infrastructure import marc_adapters, sierra_adapters


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
    bib: Dict[str, Any],
    matchpoints: List[str],
    fetcher: Optional[match_service.BibFetcher] = None,
) -> Dict[str, Any]:
    domain_bib = model.DomainBib(**bib)
    if fetcher is None:
        fetcher = get_fetcher_for_library(library=domain_bib.library)
    matcher = match_service.BibMatchService(fetcher=fetcher, matchpoints=matchpoints)
    domain_bib.bib_id = matcher.find_best_match(domain_bib)
    return domain_bib.__dict__


def process_marc_file(bib_data: BinaryIO, library: str) -> Sequence[model.DomainBib]:
    return [i for i in marc_adapters.read_marc_file(bib_data, library=library)]
