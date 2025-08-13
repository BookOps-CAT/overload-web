"""Adapter module for fetching bib records from Sierra.

Includes wrappers for `bookops_bpl_solr` and `bookops_nypl_platform` libraries.
Converts raw responses data into `DomainBib` objects.

Protocols:

`SierraSessionProtocol`
    abstracts methods required for a Sierra-compatible session.

Classes:

`SierraBibFetcher`
    converts external Sierra-style API data into domain dictionaries.
`BPLSolrSession`
    concrete implementation of `SierraSessionProtocol` for `bookops_bpl_solr`
`NYPLPlatformSession`
    concrete implementation of `SierraSessionProtocol` for `bookops_nypl_platform`
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import requests
from bookops_bpl_solr import BookopsSolrError, SolrSession
from bookops_nypl_platform import BookopsPlatformError, PlatformSession, PlatformToken

from overload_web import errors

from ... import __title__, __version__

if TYPE_CHECKING:  # pragma: no cover
    from overload_web.domain import models

logger = logging.getLogger(__name__)

AGENT = f"{__title__}/{__version__}"


class SierraBibFetcher:
    """
    Fetches bibliographic records from Sierra and converts them into domain-level
    dictionaries for `DomainBib` construction. This class is a concrete
    implementation of the `BibFetcher` protocol

    Args:
        session: a session instance implementing the Sierra protocol.
        library: the library system whose Sierra instance should be queried.
    """

    def __init__(self, library: str, session: SierraSessionProtocol | None = None):
        self.library = library
        self.session = self._get_session_for_library() if session is None else session

    def _get_session_for_library(self) -> SierraSessionProtocol:
        if self.library not in ["bpl", "nypl"]:
            raise ValueError("Invalid library. Must be 'bpl' or 'nypl'")
        elif self.library == "bpl":
            return BPLSolrSession()
        else:
            try:
                return NYPLPlatformSession()
            except BookopsPlatformError as exc:
                logger.error(f"Trouble connecting: {str(exc)}")
                raise errors.OverloadError(str(exc))

    def _response_to_domain_dict(
        self, records: list[dict[str, Any]]
    ) -> list[models.bibs.FetcherResponseDict]:
        """
        Converts raw response into dictionaries formatted for the `DomainBib` model.

        Args:
            records: list of raw bib responses from Sierra service

        Returns:
            list of cleaned domain-ready dictionaries.
        """
        if records:
            return [
                {
                    "library": self.library,
                    "orders": [],
                    "bib_id": i["id"],
                    "isbn": i.get("isbn"),
                    "oclc_number": i.get("oclc_number"),
                    "upc": i.get("upc"),
                }
                for i in records
            ]
        return []

    def get_bibs_by_id(
        self, value: str | int, key: str
    ) -> list[models.bibs.FetcherResponseDict]:
        """
        Retrieves bib records by a specific matchpoint (e.g., ISBN, OCLC)

        Args:
            value: identifier to search by.
            key: name of identifier (e.g., 'isbn', 'bib_id').

        Returns:
            list of domain-formatted dictionaries.
        """
        match_methods = {
            "bib_id": self.session._get_bibs_by_bib_id,
            "oclc_number": self.session._get_bibs_by_oclc_number,
            "isbn": self.session._get_bibs_by_isbn,
            "issn": self.session._get_bibs_by_issn,
            "upc": self.session._get_bibs_by_upc,
        }

        if key not in match_methods:
            logger.error(f"Unsupported query matchpoint: {key}")
            raise ValueError(
                f"Invalid matchpoint: '{key}'. Available matchpoints are: "
                f"{sorted([i for i in match_methods.keys()])}"
            )
        bibs = []
        if value is None:
            logger.debug(f"Skipping Sierra query on {key} with missing value.")
            return bibs
        try:
            logger.debug(
                f"Querying Sierra with {self.session.__class__.__name__} on {key} with value: {value}."
            )
            response = match_methods[key](value)
        except (BookopsPlatformError, BookopsSolrError) as exc:
            logger.error(
                f"{exc.__class__.__name__} while running Sierra queries. Closing session and aborting processing."
            )
            raise errors.OverloadError(str(exc))
        json_records = self.session._parse_response(response)
        bibs.extend(self._response_to_domain_dict(json_records))
        return bibs


@runtime_checkable
class SierraSessionProtocol(Protocol):
    """
    Protocol for Sierra-compatible sessions, ensuring expected search and response
    methods are implemented by all concrete sessions.
    """

    def _get_credentials(self) -> str | PlatformToken: ...  # pragma: no branch
    def _get_bibs_by_bib_id(
        self, value: str | int
    ) -> requests.Response: ...  # pragma: no branch
    def _get_bibs_by_isbn(
        self, value: str | int
    ) -> requests.Response: ...  # pragma: no branch
    def _get_bibs_by_issn(
        self, value: str | int
    ) -> requests.Response: ...  # pragma: no branch
    def _get_bibs_by_oclc_number(
        self, value: str | int
    ) -> requests.Response: ...  # pragma: no branch
    def _get_bibs_by_upc(
        self, value: str | int
    ) -> requests.Response: ...  # pragma: no branch
    def _parse_response(
        self, response: requests.Response
    ) -> list[dict[str, Any]]: ...  # pragma: no branch


class BPLSolrSession(SolrSession):
    """
    Adapter for querying BPL's bibliographic data via `bookops_bpl_solr`.

    Provides methods for searching by various identifiers and parsing Solr responses.
    Inherits from `bookops_bpl_solr.SolrSession`.
    """

    def __init__(self):
        super().__init__(
            authorization=self._get_credentials(),
            endpoint=os.environ["BPL_SOLR_TARGET"],
            agent=AGENT,
        )

    def _get_credentials(self) -> str:
        return os.environ["BPL_SOLR_CLIENT"]

    def _parse_response(self, response: requests.Response) -> list[dict[str, Any]]:
        bibs = []
        logger.info(f"Sierra Session response code: {response.status_code}.")
        if response and response.ok:
            logger.debug("Converting Sierra session response to json.")
            json_response = response.json()
            bibs.extend(json_response["response"]["docs"])
        return bibs

    def _get_bibs_by_bib_id(self, value: str | int) -> requests.Response:
        return self.search_bibNo(str(value))

    def _get_bibs_by_isbn(self, value: str | int) -> requests.Response:
        return self.search_isbns([str(value)])

    def _get_bibs_by_issn(self, value: str | int) -> requests.Response:
        raise NotImplementedError("Search by ISSN not implemented in BPL Solr")

    def _get_bibs_by_oclc_number(self, value: str | int) -> requests.Response:
        return self.search_controlNo(str(value))

    def _get_bibs_by_upc(self, value: str | int) -> requests.Response:
        return self.search_upcs([str(value)])


class NYPLPlatformSession(PlatformSession):
    """
    Adapter for querying NYPL's bibliographic data via `bookops_nypl_platform`.

    Implements credential handling, identifier-based searches, and response parsing.
    Inherits from `bookops_nypl_platform.PlatformSession`.
    """

    def __init__(self):
        super().__init__(
            authorization=self._get_credentials(),
            target=os.environ["NYPL_PLATFORM_TARGET"],
            agent=AGENT,
        )

    def _get_credentials(self) -> PlatformToken:
        return PlatformToken(
            os.environ["NYPL_PLATFORM_CLIENT"],
            os.environ["NYPL_PLATFORM_SECRET"],
            os.environ["NYPL_PLATFORM_OAUTH"],
            os.environ["NYPL_PLATFORM_AGENT"],
        )

    def _parse_response(self, response: requests.Response) -> list[dict[str, Any]]:
        bibs = []
        logger.info(f"Sierra Session response code: {response.status_code}.")
        if response and response.ok:
            logger.debug("Converting Sierra session response to json.")
            json_response = response.json()
            bibs.extend(json_response["data"])
        return bibs

    def _get_bibs_by_bib_id(self, value: str | int) -> requests.Response:
        return self.search_bibNos(str(value))

    def _get_bibs_by_isbn(self, value: str | int) -> requests.Response:
        return self.search_standardNos(str(value))

    def _get_bibs_by_issn(self, value: str | int) -> requests.Response:
        raise NotImplementedError("Search by ISSN not implemented in NYPL Platform")

    def _get_bibs_by_oclc_number(self, value: str | int) -> requests.Response:
        return self.search_controlNos(str(value))

    def _get_bibs_by_upc(self, value: str | int) -> requests.Response:
        return self.search_standardNos(str(value))
