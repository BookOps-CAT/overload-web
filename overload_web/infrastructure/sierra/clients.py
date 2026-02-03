"""Adapter module defining classes used to fetch bib records from Sierra.

Includes wrappers for session object in `bookops_bpl_solr` and `bookops_nypl_platform`
libraries and a class that uses these sessions to fetch bib records from Sierra.

Protocols:

`SierraSessionProtocol`
    Abstracts methods required for a Sierra-compatible session and defines interface
    for concrete implementations (e.g., `BPLSolrSession`, `NYPLPlatformSession`).

Classes:

`BPLSolrSession`
    concrete implementation of `SierraSessionProtocol` for `bookops_bpl_solr`
`NYPLPlatformSession`
    concrete implementation of `SierraSessionProtocol` for `bookops_nypl_platform`
`SierraBibFetcher`
    fetches bib records from Sierra and converts them into `BaseSierraResponse` objects
    to be used in determining best match for a `DomainBib` object.
`FetcherFactory`
    factory class to create `SierraBibFetcher` objects based on library system
    (i.e. `bpl` or `nypl`).
"""

from __future__ import annotations

import logging
import os
from typing import Protocol, runtime_checkable

import requests
from bookops_bpl_solr import BookopsSolrError, SolrSession
from bookops_nypl_platform import BookopsPlatformError, PlatformSession, PlatformToken

from overload_web.domain.models import sierra_responses

from ... import __title__, __version__

logger = logging.getLogger(__name__)

AGENT = f"{__title__}/{__version__}"


class FetcherFactory:
    """Create a `SierraBibFetcher` object"""

    def make(self, library: str) -> SierraBibFetcher:
        client: SierraSessionProtocol
        if library not in ["bpl", "nypl"]:
            raise ValueError(f"Invalid library: {library}. Must be 'bpl' or 'nypl'")
        elif library == "bpl":
            client = BPLSolrSession()
        else:
            try:
                client = NYPLPlatformSession()
            except BookopsPlatformError as exc:
                logger.error(f"Trouble connecting: {str(exc)}")
                raise
        return SierraBibFetcher(client)


class SierraBibFetcher:
    """
    Fetches bibliographic records from Sierra and converts them into domain-level
    `BaseSierraResponse` objects for `DomainBib` construction. This class is a concrete
    implementation of the `BibFetcher` protocol
    """

    def __init__(self, session: SierraSessionProtocol) -> None:
        """
        Initialize a `SierraBibFetcher` with a Sierra-compatible session.

        Args:
            session: a `SierraSessionProtocol` instance to be used to query Sierra.
        """
        self.session = session

    def get_bibs_by_id(
        self, value: str | int, key: str
    ) -> list[sierra_responses.BaseSierraResponse]:
        """
        Retrieves bib records by a specific matchpoint (e.g., isbn, oclc_number)

        Args:
            value: identifier to search by.
            key: name of identifier (e.g., 'isbn', 'bib_id').

        Returns:
            list of responses formatted as `BaseSierraResponse` objects.
        """
        match_methods = {
            "bib_id": self.session._get_bibs_by_bib_id,
            "oclc_number": self.session._get_bibs_by_oclc_number,
            "isbn": self.session._get_bibs_by_isbn,
            "issn": self.session._get_bibs_by_issn,
            "upc": self.session._get_bibs_by_upc,
        }

        if key not in match_methods:
            logger.error(f"Unsupported query matchpoint: '{key}'")
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
                f"Querying Sierra with {self.session.__class__.__name__} "
                f"on {key} with value: {value}."
            )
            response = match_methods[key](value)
        except (BookopsPlatformError, BookopsSolrError) as exc:
            logger.error(f"{exc.__class__.__name__} while running Sierra queries. ")
            raise
        bibs.extend(self.session._parse_response(response))
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
    ) -> list[sierra_responses.BaseSierraResponse]: ...  # pragma: no branch


class BPLSolrSession(SolrSession):
    """
    Adapter for querying BPL's bibliographic data via `bookops_bpl_solr`.

    Provides methods for searching by various identifiers and parsing solr responses.
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

    def _parse_response(
        self, response: requests.Response
    ) -> list[sierra_responses.BaseSierraResponse]:
        """Parse solr response into list of `BPLSolrResponse` objects."""
        logger.info(f"Sierra Session response code: {response.status_code}.")
        json_response = response.json()
        bibs = json_response["response"]["docs"]
        return [sierra_responses.BPLSolrResponse(i) for i in bibs]

    def _get_bibs_by_bib_id(self, value: str | int) -> requests.Response:
        """Search BPL Solr by bib ID."""
        return self.search_bibNo(str(value), default_response_fields=False)

    def _get_bibs_by_isbn(self, value: str | int) -> requests.Response:
        """Search BPL Solr by isbn."""
        return self.search_isbns([str(value)], default_response_fields=False)

    def _get_bibs_by_issn(self, value: str | int) -> requests.Response:
        """*Currently not implemented* Search BPL Solr by issn."""
        raise NotImplementedError("Search by ISSN not implemented in BPL Solr")

    def _get_bibs_by_oclc_number(self, value: str | int) -> requests.Response:
        """Search BPL Solr by oclc_number."""
        return self.search_controlNo(str(value), default_response_fields=False)

    def _get_bibs_by_upc(self, value: str | int) -> requests.Response:
        """Search BPL Solr by upc number."""
        return self.search_upcs([str(value)], default_response_fields=False)


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

    def _parse_response(
        self, response: requests.Response
    ) -> list[sierra_responses.BaseSierraResponse]:
        """Parse platform response into list of `NYPLPlatformResponse` objects."""
        logger.info(f"Sierra Session response code: {response.status_code}.")
        json_response = response.json()
        bibs = json_response.get("data", [])
        return [sierra_responses.NYPLPlatformResponse(i) for i in bibs]

    def _get_bibs_by_bib_id(self, value: str | int) -> requests.Response:
        """Search NYPL Platform by bib ID."""
        return self.search_bibNos(str(value))

    def _get_bibs_by_isbn(self, value: str | int) -> requests.Response:
        """Search NYPL Platform by isbn."""
        return self.search_standardNos(str(value))

    def _get_bibs_by_issn(self, value: str | int) -> requests.Response:
        """*Currently not implemented* Search NYPL Platform by issn."""
        raise NotImplementedError("Search by ISSN not implemented in NYPL Platform")

    def _get_bibs_by_oclc_number(self, value: str | int) -> requests.Response:
        """Search NYPL Platform by oclc_number."""
        return self.search_controlNos(str(value))

    def _get_bibs_by_upc(self, value: str | int) -> requests.Response:
        """Search NYPL Platform by upc number."""
        return self.search_standardNos(str(value))
