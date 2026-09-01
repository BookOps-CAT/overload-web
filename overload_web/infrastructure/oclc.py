"""Adapter module defining classes used to fetch metadata from OCLC Metadata API."""

from __future__ import annotations

import logging
import os
from typing import Any, Protocol, runtime_checkable

from bookops_worldcat import MetadataSession, WorldcatAccessToken
from bookops_worldcat.errors import BookopsWorldcatError
from requests import Request, Response

from .. import __title__, __version__

logger = logging.getLogger(__name__)

AGENT = f"{__title__}/{__version__}"


class WorldcatFetcher(MetadataSession):
    """
    Fetches bibliographic record data from OCLC.
    This class is a concrete implementation of the `OCLCBibFetcher` protocol.
    """

    def __init__(self, session: OclcSessionProtocol) -> None:
        """
        Initialize a `WorldcatFetcher` with a Metadata API-compatible session.

        Args:
            session: a `OclcSessionProtocol` instance to be used to query OCLC API.
        """
        self.session = session

    def get_brief_bibs_by_id(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        try:
            response = self.session._brief_bibs_get_by_id(params=params)
        except BookopsWorldcatError as exc:
            logger.error(f"{exc.__class__.__name__} while running Worldcat queries.")
            raise
        return self.session._parse_brief_record_response(response)

    def get_full_bib_by_id(self, value: str) -> bytes:
        try:
            response = self.session._full_bib_get_by_id(value)
            return response.content
        except BookopsWorldcatError as exc:
            logger.error(f"{exc.__class__.__name__} while running Worldcat queries.")
            raise

    def get_full_bib_json_by_id(self, value: str) -> dict[str, Any]:
        try:
            response = self.session._full_bib_json_get_by_id(value)
            return response.json()
        except BookopsWorldcatError as exc:
            logger.error(f"{exc.__class__.__name__} while running Worldcat queries.")
            raise


class OclcSession(MetadataSession):
    def __init__(self, library: str):
        super().__init__(authorization=self._get_credentials(library), agent=AGENT)

    def _get_credentials(self, library: str) -> WorldcatAccessToken:
        lib = library.upper()
        return WorldcatAccessToken(
            key=os.environ[f"{lib}_WORLDCAT_CLIENT"],
            secret=os.environ[f"{lib}_WORLDCAT_SECRET"],
            scopes="wcapi",
        )

    def _check_authorization(self) -> None:
        if self.authorization.is_expired():
            self._get_new_access_token()

    def _parse_brief_record_response(self, response: Response) -> list[dict[str, Any]]:
        json_response = response.json()
        rec_count = int(json_response["numberOfRecords"])
        logger.debug(
            f"MetadataSession returned {rec_count} record(s). Returning first 50."
        )
        return json_response["briefRecords"]

    def _prepare_and_send_request(self, request: Request) -> Response:
        prepared_request = self.prepare_request(request)
        return self.send(prepared_request)

    def _brief_bibs_get_by_id(self, params: dict[str, Any]) -> Response:
        logger.debug(f"Querying WorldCat for brief bibs with query `{params['q']}`.")
        self._check_authorization()
        url = self._url_search_brief_bibs()
        header = {"Accept": "application/json"}
        req = Request("GET", url, params=params, headers=header)
        response = self._prepare_and_send_request(req)
        return response

    def _full_bib_get_by_id(self, value: str) -> Response:
        logger.debug(f"Querying WorldCat for full MARC record for {value}.")
        self._check_authorization()
        url = self._url_manage_bibs(value)
        header = {"Accept": "application/marc"}
        req = Request("GET", url, headers=header)
        response = self._prepare_and_send_request(req)
        return response

    def _full_bib_json_get_by_id(self, value: str) -> Response:
        logger.debug(f"Querying WorldCat for full bib record in json for {value}.")
        self._check_authorization()
        url = self._url_search_bibs(value)
        header = {"Accept": "application/json"}
        req = Request("GET", url, headers=header)
        response = self._prepare_and_send_request(req)
        return response


@runtime_checkable
class OclcSessionProtocol(Protocol):
    """
    Protocol for Metadata API-compatible sessions, ensuring expected search
    and response methods are implemented by all concrete sessions.
    """

    def _get_credentials(
        self, library: str
    ) -> WorldcatAccessToken: ...  # pragma: no branch
    def _check_authorization(self) -> None: ...  # pragma: no branch
    def _parse_brief_record_response(
        self, response: Response
    ) -> list[dict[str, Any]]: ...  # pragma: no branch
    def _prepare_and_send_request(
        self, request: Request
    ) -> Response: ...  # pragma: no branch
    def _brief_bibs_get_by_id(
        self, params: dict[str, Any]
    ) -> Response: ...  # pragma: no branch
    def _full_bib_get_by_id(self, value: str) -> Response: ...  # pragma: no branch
    def _full_bib_json_get_by_id(self, value: str) -> Response: ...  # pragma: no branch
