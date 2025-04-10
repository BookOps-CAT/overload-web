from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List

import requests
from bookops_bpl_solr import SolrSession
from bookops_nypl_platform import PlatformSession, PlatformToken

from overload_web.domain import model

from .. import __title__, __version__

logger = logging.getLogger(__name__)

AGENT = f"{__title__}/{__version__}"


class SierraService:
    def __init__(self, session: AbstractSierraSession):
        self.session = session

    def get_bibs_by_id(self, bib: model.DomainBib, key: str) -> List[Dict[str, Any]]:
        return self.session.get_bibs_by_id(key, getattr(bib, f"{key}"))


class AbstractSierraSession(ABC):
    @abstractmethod
    def _get_credentials(self) -> str | PlatformToken:
        raise NotImplementedError("Subclasses should implement this method.")

    @abstractmethod
    def _get_target(self) -> str:
        raise NotImplementedError("Subclasses should implement this method.")

    @abstractmethod
    def _get_bibs_by_id(self, key: str, value: str | int) -> List[Dict[str, Any]]:
        raise NotImplementedError("Subclasses should implement this method.")

    def get_bibs_by_id(self, key: str, value: str | int) -> List[Dict[str, Any]]:
        return self._get_bibs_by_id(key=key, value=value)


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

    def _get_bibs_by_id(self, key: str, value: str | int) -> List[Dict[str, Any]]:
        response: requests.Response
        if key == "bib_id":
            response = self.search_bibNo(str(value))
        elif key == "oclc_number":
            response = self.search_controlNo(str(value))
        elif key == "isbn":
            response = self.search_isbns([str(value)])
        elif key == "upc":
            response = self.search_upcs([str(value)])
        else:
            raise ValueError(
                "Invalid matchpoint. Available matchpoints are: bib_id, "
                "oclc_number, isbn, and upc"
            )
        bibs = []
        if response and response.ok:
            json_response = response.json()
            bibs.extend(json_response["response"]["docs"])
        return bibs


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

    def _get_bibs_by_id(self, key: str, value: str | int) -> List[Dict[str, Any]]:
        response: requests.Response
        if key == "bib_id":
            response = self.search_bibNos(str(value))
        elif key == "oclc_number":
            response = self.search_controlNos(str(value))
        elif key == "isbn":
            response = self.search_standardNos(str(value))
        elif key == "upc":
            response = self.search_standardNos(str(value))
        else:
            raise ValueError(
                "Invalid matchpoint. Available matchpoints are: bib_id, "
                "oclc_number, isbn, and upc"
            )
        bibs = []
        if response and response.ok:
            json_response = response.json()
            bibs.extend(json_response["data"])
        return bibs
