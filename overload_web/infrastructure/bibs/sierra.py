"""Adapter module for fetching bib records from Sierra.

Includes wrappers for `bookops_bpl_solr` and `bookops_nypl_platform` libraries.
Converts raw responses data into domain-level structures expected by the `DomainBib`
model.

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
from typing import Any, Optional, Protocol, Union, runtime_checkable

import requests
from bookops_bpl_solr import SolrSession
from bookops_nypl_platform import PlatformSession, PlatformToken

from ... import __title__, __version__

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

    def __init__(self, library: str, session: Optional[SierraSessionProtocol] = None):
        self.library = library
        self.session = self._get_session_for_library() if session is None else session

    def _get_session_for_library(self) -> SierraSessionProtocol:
        if self.library not in ["bpl", "nypl"]:
            raise ValueError("Invalid library. Must be 'bpl' or 'nypl'")
        elif self.library == "bpl":
            return BPLSolrSession()
        else:
            return NYPLPlatformSession()

    def _response_to_domain_dict(
        self, records: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
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

    def get_bibs_by_id(self, value: Union[str, int], key: str) -> list[dict[str, Any]]:
        """
        Retrieves bib records by a specific matchpoint (e.g., ISBN, OCLC)

        Args:
            value: identifier to search by.
            key: name of identifier (e.g., 'isbn', 'bib_id').

        Returns:
            list of domain-formatted bibliographic dictionaries.
        """
        match_methods = {
            "bib_id": self.session._get_bibs_by_bib_id,
            "oclc_number": self.session._get_bibs_by_oclc_number,
            "isbn": self.session._get_bibs_by_isbn,
            "issn": self.session._get_bibs_by_issn,
            "upc": self.session._get_bibs_by_upc,
        }

        if key not in match_methods:
            raise ValueError(
                f"Invalid matchpoint: '{key}'. Available matchpoints are: "
                f"{sorted([i for i in match_methods.keys()])}"
            )
        bibs = []
        if value is not None:
            response = match_methods[key](value)
            json_records = self.session._parse_response(response)
            bibs.extend(self._response_to_domain_dict(json_records))
        return bibs


@runtime_checkable
class SierraSessionProtocol(Protocol):
    """
    Protocol for Sierra-compatible sessions, ensuring expected search and response
    methods are implemented by all concrete sessions.
    """

    def _get_credentials(self) -> str | PlatformToken: ...
    def _get_bibs_by_bib_id(self, value: Union[str, int]) -> requests.Response: ...
    def _get_bibs_by_isbn(self, value: Union[str, int]) -> requests.Response: ...
    def _get_bibs_by_issn(self, value: Union[str, int]) -> requests.Response: ...
    def _get_bibs_by_oclc_number(self, value: Union[str, int]) -> requests.Response: ...
    def _get_bibs_by_upc(self, value: Union[str, int]) -> requests.Response: ...
    def _parse_response(self, response: requests.Response) -> list[dict[str, Any]]: ...


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
        if response and response.ok:
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
        if response and response.ok:
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
