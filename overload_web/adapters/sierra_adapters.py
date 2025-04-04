from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import List

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

    def get_all_bib_ids(
        self, order_bib: model.OrderBib, match_keys: List[str]
    ) -> List[str]:
        bibs = []
        for key in match_keys:
            bibs = self.session.get_bibs_by_id(key, getattr(order_bib, f"{key}"))
            if not bibs:
                continue
        return bibs


class AbstractSierraSession(ABC):
    @abstractmethod
    def _get_credentials(self) -> str | PlatformToken:
        pass

    @abstractmethod
    def _get_target(self) -> str:
        pass

    @abstractmethod
    def _get_bibs_by_id(self, key: str, value: str | int) -> List[str]:
        pass

    def get_bibs_by_id(self, key: str, value: str | int) -> List[str]:
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

    def _get_bibs_by_id(self, key: str, value: str | int) -> List[str]:
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
        bib_ids = []
        if response and response.ok:
            json_response = response.json()
            bib_ids.extend([i["id"] for i in json_response["response"]["docs"]])
        return bib_ids


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

    def _get_bibs_by_id(self, key: str, value: str | int) -> List[str]:
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
        bib_ids = []
        if response and response.ok:
            json_response = response.json()
            bib_ids.extend([i["id"] for i in json_response["data"]])
        return bib_ids
