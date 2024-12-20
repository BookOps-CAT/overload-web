from __future__ import annotations

from abc import ABC, abstractmethod
import logging
import os
from typing import List, Optional

from bookops_nypl_platform import PlatformSession, PlatformToken
from bookops_bpl_solr import SolrSession

from . import __title__, __version__

logger = logging.getLogger(__name__)

AGENT = f"{__title__}/{__version__}"


class AbstractSierraSession(ABC):
    @abstractmethod
    def _get_credentials(self) -> str | PlatformToken:
        pass

    @abstractmethod
    def _get_target(self) -> str:
        pass

    @abstractmethod
    def _search_by_id(self, key: str, value: str | int) -> Optional[List[str]]:
        pass

    def get_all_bib_ids(self, key: str, value: str | int) -> Optional[List]:
        return self._search_by_id(key=key, value=value)

    def get_bib_id(self, key: str, value: str | int) -> Optional[str]:
        response = self._search_by_id(key=key, value=value)
        if not response:
            return None
        else:
            return response[0]


class BPLSolrSession(SolrSession, AbstractSierraSession):
    def __init__(self):
        super().__init__(
            authorization=self._get_credentials(),
            endpoint=self._get_target(),
            agent=AGENT,
        )

    def _get_credentials(self) -> str:
        return os.environ["BPL_SOLR_CLIENT_KEY"]

    def _get_target(self) -> str:
        return os.environ["BPL_SOLR_ENDPOINT"]

    def _search_by_id(self, key: str, value: str | int) -> Optional[List[str]]:
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
        if response and response.ok:
            json_response = response.json()["response"]
            return [i["id"] for i in json_response["docs"]]
        else:
            return None


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

    def _search_by_id(self, key: str, value: str | int) -> Optional[List[str]]:
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
        if response and response.ok:
            json_response = response.json()["data"]
            return [i["id"] for i in json_response]
        else:
            return None
