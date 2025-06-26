"""Application service functions for matching bib records and applying templates.

Functions coordinate interactions between domain models, infrastructure adapters,
and presentation layer.
"""

from __future__ import annotations

import io
import logging
from typing import Any, BinaryIO, Dict, List, Optional

from overload_web.application import dto
from overload_web.application.services import unit_of_work
from overload_web.domain import logic, models, protocols
from overload_web.infrastructure import bibs
from overload_web.infrastructure.bibs import marc_adapters

logger = logging.getLogger(__name__)


def attach_template(
    bibs: List[dto.bib.BibDTO], template: Dict[str, Any]
) -> List[dto.bib.BibDTO]:
    """
    Applies template data to a list of bib records.

    Args:
        bibs: list of data transfer objects containing marc data.
        template: dictionary of template data to apply.

    Returns:
        list of data transfer objects with the template data applied
    """
    processed_bibs = []
    for bib in bibs:
        bib.domain_bib.apply_template(template_data=template)
        bib.update_order_fields()
        processed_bibs.append(bib)
    return processed_bibs


def get_fetcher_for_library(library: str) -> protocols.bibs.BibFetcher:
    """
    Creates a `SierraBibFetcher` object for the specified library.

    Args:
        library: library whose Sierra instance should be queried ("bpl" or "nypl")

    Returns:
        a `BibFetcher` object for the given library.

    Raises:
        ValueError: if the library is not "bpl" or "nypl".
    """
    session: bibs.sierra.SierraSessionProtocol
    if library == "bpl":
        session = bibs.sierra.BPLSolrSession()
    elif library == "nypl":
        session = bibs.sierra.NYPLPlatformSession()
    else:
        raise ValueError("Invalid library. Must be 'bpl' or 'nypl'")
    return bibs.sierra.SierraBibFetcher(session=session, library=library)


def match_bibs(
    bibs: List[dto.bib.BibDTO],
    library: str,
    matchpoints: List[str],
    fetcher: Optional[protocols.bibs.BibFetcher] = None,
) -> List[dto.bib.BibDTO]:
    """
    Matches bib records from an incoming MARC file against Sierra.

    Args:
        bibs: list of data transfer objects containing marc data.
        library: library to whom the records belong.
        matchpoints: fields to use for matching.
        fetcher: optional custom fetcher; created automatically if not provided.

    Returns:
        list of `BibDTO` objects.
    """
    if fetcher is None:
        fetcher = get_fetcher_for_library(library=library)
    matcher = logic.bibs.BibMatcher(fetcher=fetcher, matchpoints=matchpoints)

    processed_bibs = []
    for bib in bibs:
        bib.domain_bib = matcher.match_bib(bib.domain_bib)
        bib.update_bib_fields()
        processed_bibs.append(bib)
    return processed_bibs


def read_marc_binary(file_data: BinaryIO, library: str) -> List[dto.bib.BibDTO]:
    """
    Reads a MARC binary file and returns a list of `BibDTO` objects.

    Args:

        file_data: binary stream containing MARC data.
        library: the library to whom the records belong.

    Returns:
        list of `BibDTO` objects.
    """
    bibs = marc_adapters.read_marc_file(marc_file=file_data, library=library)
    return bibs


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
    template = models.templates.Template(**data)
    if not template.name or not template.name.strip():
        raise ValueError("Templates must have a name before being saved.")
    if not template.agent or not template.agent.strip():
        raise ValueError("Templates must have an agent before being saved.")
    with uow:
        uow.templates.save(template=template)
        uow.commit()
    return template.__dict__


def write_marc_binary(bibs: List[dto.bib.BibDTO]) -> io.BytesIO:
    """
    Writes a list of data transfer objects to a file in MARC format.

    Args:
        file: the name of the file to write to.

    Returns:
        list of bibs as BytesIO object.
    """
    io_data = io.BytesIO()
    for bib in bibs:
        io_data.write(bib.bib.as_marc())
    io_data.seek(0)
    return io_data
