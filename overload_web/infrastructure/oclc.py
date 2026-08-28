"""Adapter module defining classes used to fetch metadata from OCLC Metadata API."""

from __future__ import annotations

import logging
import os
from typing import Any

from bookops_worldcat import MetadataSession, WorldcatAccessToken
from bookops_worldcat.errors import BookopsWorldcatError
from requests import Request, Response

from .. import __title__, __version__

logger = logging.getLogger(__name__)

AGENT = f"{__title__}/{__version__}"


class WorldcatFetcher(MetadataSession):
    def __init__(self, library: str):
        super().__init__(authorization=self._get_credentials(library), agent=AGENT)

    def _get_credentials(self, library: str) -> WorldcatAccessToken:
        lib = library.upper()
        return WorldcatAccessToken(
            key=os.environ[f"{lib}_WORLDCAT_CLIENT"],
            secret=os.environ[f"{lib}_WORLDCAT_SECRET"],
            scopes=os.environ["WORLDCAT_SCOPES"],
        )

    def _parse_response(self, response: Response) -> list[dict[str, Any]]:
        logger.info(f"MetadataSession response code: {response.status_code}.")
        json_response = response.json()
        rec_count = int(json_response["numberOfRecords"])
        logger.debug(
            f"MetadataSession returned {rec_count} record(s). Returning first 50."
        )
        return json_response["briefRecords"]

    def _brief_bib_get_by_id(self, params: dict[str, Any]) -> Response:
        if self.authorization.is_expired():
            self._get_new_access_token()
        url = self._url_search_brief_bibs()
        header = {"Accept": "application/json"}
        req = Request("GET", url, params=params, headers=header)
        prepared_request = self.prepare_request(req)

        response = self.send(prepared_request)

        return response

    def _full_bib_get_by_id(self, oclc_number: str) -> Response:
        if self.authorization.is_expired():
            self._get_new_access_token()
        url = self._url_manage_bibs(oclc_number)
        header = {"Accept": "application/marc"}
        req = Request("GET", url, headers=header)
        prepared_request = self.prepare_request(req)

        response = self.send(prepared_request)

        return response

    def _full_bib_json_get_by_id(self, oclc_number: str) -> Response:
        if self.authorization.is_expired():
            self._get_new_access_token()
        url = self._url_search_bibs(oclc_number)
        header = {"Accept": "application/marc"}
        req = Request("GET", url, headers=header)
        prepared_request = self.prepare_request(req)

        response = self.send(prepared_request)

        return response

    def get_brief_bibs_by_id(
        self,
        index: str,
        value: str | int,
        cat_agency: str | None = None,
        format: str | None = None,
    ) -> list[dict[str, Any]]:
        payload = {"q": f"{index}={value}", "inCatalogLanguage": "eng", "limit": 50}
        if cat_agency:
            payload["catalogSource"] = cat_agency
        if format:
            payload["itemSubType"] = format
        logger.debug(f"Querying WorldCat for brief bibs with query `{index}={value}`.")
        bibs = []
        try:
            response = self._brief_bib_get_by_id(params=payload)
        except BookopsWorldcatError as exc:
            logger.error(f"{exc.__class__.__name__} while running Worldcat queries.")
            raise
        bibs.extend(self._parse_response(response))
        return bibs

    def get_full_bib_by_id(self, value: str) -> bytes:
        logger.debug(f"Querying WorldCat for full MARC record for {value}.")
        try:
            response = self._full_bib_get_by_id(value)
            return response.content
        except BookopsWorldcatError as exc:
            logger.error(f"{exc.__class__.__name__} while running Worldcat queries.")
            raise

    def get_full_bib_json_by_id(self, value: str) -> dict[str, Any]:
        logger.debug(f"Querying WorldCat for full bib record in json for {value}.")
        try:
            response = self._full_bib_json_get_by_id(value)
            return response.json()
        except BookopsWorldcatError as exc:
            logger.error(f"{exc.__class__.__name__} while running Worldcat queries.")
            raise
