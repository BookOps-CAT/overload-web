"""Application service functions for matching bib records and applying templates.

Functions coordinate interactions between domain models, infrastructure adapters,
and presentation layer.
"""

from __future__ import annotations

from typing import Any, BinaryIO, Dict, List, Optional

from overload_web.application import unit_of_work
from overload_web.domain import bib_matcher, model
from overload_web.infrastructure import marc_adapters, sierra_adapters


def apply_template_data(
    bib_data: List[Dict[str, Any]], template: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Applies template data to a list of bib records.

    Args:
        bib_data: list of bibliographic records as dicts.
        template: dictionary of template data to apply.

    Returns:
        list of processed records with the template data applied
    """
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


def get_fetcher_for_library(library: str) -> bib_matcher.BibFetcher:
    """
    Creates a `SierraBibFetcher` object for the specified library.

    Args:
        library: library whose Sierra instance should be queried ("bpl" or "nypl")

    Returns:
        a `BibFetcher` object for the given library.

    Raises:
        ValueError: if the library is not "bpl" or "nypl".
    """
    session: sierra_adapters.SierraSessionProtocol
    if library == "bpl":
        session = sierra_adapters.BPLSolrSession()
    elif library == "nypl":
        session = sierra_adapters.NYPLPlatformSession()
    else:
        raise ValueError("Invalid library. Must be 'bpl' or 'nypl'")
    return sierra_adapters.SierraBibFetcher(session=session, library=library)


def match_bibs(
    file_data: BinaryIO,
    library: str,
    matchpoints: List[str],
    fetcher: Optional[bib_matcher.BibFetcher] = None,
) -> List[Dict[str, Any]]:
    """
    Matches bib records from an incoming MARC file against Sierra.

    Args:
        file_data: list of MARC records as a `BinaryIO` object
        library: library to whom the records belong.
        matchpoints: fields to use for matching.
        fetcher: optional custom fetcher; created automatically if not provided.

    Returns:
        list of records as dicts with newly matched bib IDs.
    """
    if fetcher is None:
        fetcher = get_fetcher_for_library(library=library)
    matcher = bib_matcher.BibMatchService(fetcher=fetcher, matchpoints=matchpoints)

    processed_bibs = []
    bibs = marc_adapters.read_marc_file(marc_file=file_data, library=library)
    for bib in bibs:
        bib.bib_id = matcher.find_best_match(bib)
        processed_bibs.append(bib)
    return [i.__dict__ for i in processed_bibs]


def match_and_attach(
    file_data: BinaryIO,
    library: str,
    template: Optional[Dict[str, Any]],
    matchpoints: List[str],
    fetcher: Optional[bib_matcher.BibFetcher] = None,
) -> List[Dict[str, Any]]:
    """
    Matches bib records from an incoming MARC file against Sierra and optionally
    applies data from a template.

    Args:
        file_data: list of MARC records as a `BinaryIO` object
        library: library to whom the records belong.
        template: optional template data to apply.
        matchpoints: fields to use for matching.
        fetcher: optional custom fetcher; created automatically if not provided.

    Returns:
        list of processed bibs as dicts.
    """
    if fetcher is None:
        fetcher = get_fetcher_for_library(library=library)
    matcher = bib_matcher.BibMatchService(fetcher=fetcher, matchpoints=matchpoints)

    processed_bibs = []
    bibs = marc_adapters.read_marc_file(marc_file=file_data, library=library)
    for bib in bibs:
        bib.bib_id = matcher.find_best_match(bib)
        if template:
            bib.apply_template(template_data=template)
        processed_bibs.append(bib)
    return [i.__dict__ for i in processed_bibs]


def save_template(
    data: Dict[str, Any], uow: unit_of_work.UnitOfWorkProtocol
) -> Dict[str, Any]:
    """
    Validates and persists a new template using a unit of work.

    Args:
        data: dictionary of template fields.
        uow: unit of work to use to manage the transaction.

    Returns:
        the saved template as a dict.

    Raises:
        ValueError: If the template lacks `name` or `agent`.
    """
    template = model.Template(**data)
    if not template.name or not template.name.strip():
        raise ValueError("Templates must have a name before being saved.")
    if not template.agent or not template.agent.strip():
        raise ValueError("Templates must have an agent before being saved.")
    with uow:
        uow.templates.save(template=template)
        uow.commit()
    return template.__dict__
