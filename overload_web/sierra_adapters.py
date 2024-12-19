from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from typing import Dict, List, Optional

from bookops_nypl_platform import PlatformSession, PlatformToken
from bookops_bpl_solr import SolrSession

from . import __title__, __version__

logger = logging.getLogger(__name__)

AGENT = f"{__title__}/{__version__}"


class AbstractSierraSession(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def _match_order(self, matchpoints: Dict[str, str]) -> Optional[List[str]]:
        pass

    def match_bib(self, matchpoints: Dict[str, str]) -> Optional[str]:
        bibs = self._match_order(matchpoints)
        if bibs:
            return bibs[0]
        else:
            return None

    def order_matches(self, matchpoints: Dict[str, str]) -> Optional[List[str]]:
        return self._match_order(matchpoints)


class BPLSolrSession(SolrSession, AbstractSierraSession):
    def __init__(
        self,
        authorization: str,
        endpoint: str = "solr_endpoint",
    ):
        super().__init__(authorization, endpoint=endpoint, agent=AGENT)

    def _match_order(self, matchpoints: Dict[str, str]) -> Optional[List[str]]:
        hit = None
        json_response = None
        for k, v in matchpoints.items():
            if k == "bib_id":
                hit = self.search_bibNo(str(v))
            elif k == "oclc_number":
                hit = self.search_controlNo(str(v))
            elif k == "isbn":
                hit = self.search_isbns([str(v)])
            elif k == "upc":
                hit = self.search_upcs([str(v)])
            else:
                raise ValueError(
                    "Invalid matchpoint. Available matchpoints are: bib_id, "
                    "oclc_number, isbn, and upc"
                )
            if hit and hit.ok:
                json_response = hit.json()["response"]
                break
            else:
                continue
        if isinstance(json_response, dict):
            return [i["id"] for i in json_response["docs"]]
        else:
            return json_response


class NYPLPlatformSession(PlatformSession, AbstractSierraSession):
    def __init__(
        self,
        authorization: PlatformToken,
        target: str = "prod",
    ):
        super().__init__(authorization, target=target, agent=AGENT)

    def _match_order(self, matchpoints: Dict[str, str]) -> Optional[List[str]]:
        hit = None
        json_response = None
        for k, v in matchpoints.items():
            if k == "bib_id":
                hit = self.search_bibNos(str(v))
            elif k == "oclc_number":
                hit = self.search_controlNos(str(v))
            elif k == "isbn":
                hit = self.search_standardNos(str(v))
            elif k == "upc":
                hit = self.search_standardNos(str(v))
            else:
                raise ValueError(
                    "Invalid matchpoint. Available matchpoints are: bib_id, "
                    "oclc_number, isbn, and upc"
                )
            if hit and hit.ok:
                json_response = hit.json()["data"]
                break
            else:
                continue
        if isinstance(json_response, list):
            return [i["id"] for i in json_response]
        else:
            return json_response
