from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from typing import List, Optional

from bookops_nypl_platform import PlatformSession, PlatformToken
from bookops_bpl_solr import SolrSession

from overload_web.domain import model

from . import __title__, __version__

logger = logging.getLogger(__name__)

AGENT = f"{__title__}/{__version__}"


class AbstractSierraSession(ABC):
    def __init__(self):
        pass

    def match_order(
        self, order: model.Order, matchpoints: List[str]
    ) -> Optional[List[str]]:
        return self._match_order(order, matchpoints)

    @abstractmethod
    def _match_order(
        self, order: model.Order, matchpoints: List[str]
    ) -> Optional[List[str]]:
        pass


class BPLSolrSession(SolrSession, AbstractSierraSession):
    def __init__(
        self,
        authorization: str,
        endpoint: str = "solr_endpoint",
    ):
        super().__init__(authorization, endpoint=endpoint, agent=AGENT)

    def _match_order(
        self, order: model.Order, matchpoints: List[str]
    ) -> Optional[List[str]]:
        hit = None
        json_response = None
        for matchpoint in matchpoints:
            if matchpoint == "bib_id":
                hit = self.search_bibNo(str(order.bib_id))
            elif matchpoint == "oclc_number":
                hit = self.search_controlNo(str(order.oclc_number))
            elif matchpoint == "isbn":
                hit = self.search_isbns([str(order.isbn)])
            elif matchpoint == "upc":
                hit = self.search_upcs([str(order.upc)])
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

    def _match_order(
        self, order: model.Order, matchpoints: List[str]
    ) -> Optional[List[str]]:
        hit = None
        json_response = None
        for matchpoint in matchpoints:
            if matchpoint == "bib_id":
                hit = self.search_bibNos(str(order.bib_id))
            elif matchpoint == "oclc_number":
                hit = self.search_controlNos(str(order.oclc_number))
            elif matchpoint == "isbn":
                hit = self.search_standardNos(str(order.isbn))
            elif matchpoint == "upc":
                hit = self.search_standardNos(str(order.upc))
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
