from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Union

import requests
from bookops_bpl_solr import SolrSession
from bookops_nypl_platform import PlatformSession, PlatformToken

from .. import __title__, __version__

logger = logging.getLogger(__name__)

AGENT = f"{__title__}/{__version__}"


class SierraServiceFactory:
    def get_session(self, library: str) -> Callable[[], AbstractSierraSession]:
        session: Callable[[], AbstractSierraSession]
        if library == "bpl":
            session = BPLSolrSession
        elif library == "nypl":
            session = NYPLPlatformSession
        else:
            raise ValueError("Invalid library. Must be 'bpl' or 'nypl'")
        return session


class AbstractService:
    @abstractmethod
    def _get_bibs_by_id(self, value: Union[str, int], key: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("Subclasses should implement this method.")

    def get_bibs_by_id(
        self, value: Union[str, int, None], key: str
    ) -> List[Dict[str, Any]]:
        bibs = []
        if value is not None:
            bibs.extend(self._get_bibs_by_id(value=value, key=key))
        return bibs


class SierraService(AbstractService):
    def __init__(self, session: AbstractSierraSession):
        self.session = session

    def _get_bibs_by_id(self, value: Union[str, int], key: str) -> List[Dict[str, Any]]:
        if key == "bib_id":
            response = self.session._get_bibs_by_bib_id(value=value)
        elif key == "oclc_number":
            response = self.session._get_bibs_by_oclc_number(value=value)
        elif key == "isbn":
            response = self.session._get_bibs_by_isbn(value=value)
        elif key == "issn":
            response = self.session._get_bibs_by_issn(value=value)
        elif key == "upc":
            response = self.session._get_bibs_by_upc(value=value)
        else:
            raise ValueError(
                "Invalid matchpoint. Available matchpoints are: bib_id, "
                "oclc_number, isbn, issn, and upc"
            )
        bibs = self.session._parse_response(response=response)
        return bibs


class AbstractSierraSession(ABC):
    @abstractmethod
    def _get_credentials(self) -> str | PlatformToken:
        raise NotImplementedError("Subclasses should implement this method.")

    @abstractmethod
    def _get_target(self) -> str:
        raise NotImplementedError("Subclasses should implement this method.")

    @abstractmethod
    def _get_bibs_by_bib_id(self, value: str | int) -> requests.Response:
        raise NotImplementedError("Subclasses should implement this method.")

    @abstractmethod
    def _get_bibs_by_isbn(self, value: str | int) -> requests.Response:
        raise NotImplementedError("Subclasses should implement this method.")

    @abstractmethod
    def _get_bibs_by_issn(self, value: str | int) -> requests.Response:
        raise NotImplementedError("Subclasses should implement this method.")

    @abstractmethod
    def _get_bibs_by_oclc_number(self, value: str | int) -> requests.Response:
        raise NotImplementedError("Subclasses should implement this method.")

    @abstractmethod
    def _get_bibs_by_upc(self, value: str | int) -> requests.Response:
        raise NotImplementedError("Subclasses should implement this method.")

    @abstractmethod
    def _parse_response(self, response: requests.Response) -> List[Dict[str, Any]]:
        raise NotImplementedError("Subclasses should implement this method.")


class BPLSolrSession(SolrSession, AbstractSierraSession):
    def __init__(self):
        super().__init__(
            authorization=self._get_credentials(),
            endpoint=self._get_target(),
            agent=AGENT,
        )

    def _get_credentials(self) -> str:
        return os.environ["BPL_SOLR_CLIENT"]

    def _get_target(self) -> str:
        return os.environ["BPL_SOLR_TARGET"]

    def _parse_response(self, response: requests.Response) -> List[Dict[str, Any]]:
        bibs = []
        if response and response.ok:
            json_response = response.json()
            bibs.extend(json_response["response"]["docs"])
        return bibs

    def _get_bibs_by_bib_id(self, value: str | int) -> requests.Response:
        response = self.search_bibNo(str(value))
        return response

    def _get_bibs_by_isbn(self, value: str | int) -> requests.Response:
        response = self.search_isbns([str(value)])
        return response

    def _get_bibs_by_issn(self, value: str | int) -> requests.Response:
        raise NotImplementedError("Search by ISSN not implemented in BPL Solr")

    def _get_bibs_by_oclc_number(self, value: str | int) -> requests.Response:
        response = self.search_controlNo(str(value))
        return response

    def _get_bibs_by_upc(self, value: str | int) -> requests.Response:
        response = self.search_upcs([str(value)])
        return response


class NYPLPlatformSession(PlatformSession, AbstractSierraSession):
    def __init__(self):
        super().__init__(
            authorization=self._get_credentials(),
            target=self._get_target(),
            agent=AGENT,
        )

    def _get_credentials(self) -> PlatformToken:
        return PlatformToken(
            os.environ["NYPL_PLATFORM_CLIENT"],
            os.environ["NYPL_PLATFORM_SECRET"],
            os.environ["NYPL_PLATFORM_OAUTH"],
            os.environ["NYPL_PLATFORM_AGENT"],
        )

    def _get_target(self) -> str:
        return os.environ["NYPL_PLATFORM_TARGET"]

    def _parse_response(self, response: requests.Response) -> List[Dict[str, Any]]:
        bibs = []
        if response and response.ok:
            json_response = response.json()
            bibs.extend(json_response["data"])
        return bibs

    def _get_bibs_by_bib_id(self, value: str | int) -> requests.Response:
        response = self.search_bibNos(str(value))
        return response

    def _get_bibs_by_isbn(self, value: str | int) -> requests.Response:
        response = self.search_standardNos(str(value))
        return response

    def _get_bibs_by_issn(self, value: str | int) -> requests.Response:
        raise NotImplementedError("Search by ISSN not implemented in NYPL Platform")

    def _get_bibs_by_oclc_number(self, value: str | int) -> requests.Response:
        response = self.search_controlNos(str(value))
        return response

    def _get_bibs_by_upc(self, value: str | int) -> requests.Response:
        response = self.search_standardNos(str(value))
        return response
