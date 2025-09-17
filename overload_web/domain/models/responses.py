"""Domain models that define responses from Sierra"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypedDict

from ... import __title__, __version__

if TYPE_CHECKING:  # pragma: no cover
    pass
logger = logging.getLogger(__name__)

AGENT = f"{__title__}/{__version__}"


class FetcherResponseDict(TypedDict):
    """Defines the dict returned by `BibFetcher.get_bibs_by_id` method"""

    barcodes: list[str]
    bib_id: str
    branch_call_number: list[str]
    cat_source: str
    collection: str | None
    control_number: str | None
    isbn: list[str]
    library: str
    oclc_number: list[str]
    research_call_number: list[str]
    title: str
    upc: list[str]
    update_date: str | None
    var_fields: list[dict[str, Any]]


class BaseSierraResponse(ABC):
    library: str

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        self.bib_id: str = data["id"]
        self.library = self.__class__.library
        self.title: str = data["title"]

    @property
    @abstractmethod
    def barcodes(self) -> list[str]: ...  # pragma: no branch

    @property
    @abstractmethod
    def branch_call_number(self) -> list[str]: ...  # pragma: no branch

    @property
    @abstractmethod
    def cat_source(self) -> str: ...  # pragma: no branch

    @property
    @abstractmethod
    def collection(self) -> str | None: ...  # pragma: no branch

    @property
    def control_number(self) -> str | None: ...  # pragma: no branch

    @property
    @abstractmethod
    def isbn(self) -> list[str]: ...  # pragma: no branch

    @property
    @abstractmethod
    def oclc_number(self) -> list[str]: ...  # pragma: no branch

    @property
    @abstractmethod
    def research_call_number(self) -> list[str]: ...  # pragma: no branch

    @property
    @abstractmethod
    def upc(self) -> list[str]: ...  # pragma: no branch

    @property
    @abstractmethod
    def update_date(self) -> str | None: ...  # pragma: no branch

    @property
    @abstractmethod
    def var_fields(self) -> list[dict[str, Any]]: ...  # pragma: no branch

    def to_dict(self) -> FetcherResponseDict:
        return {
            "title": self.title,
            "barcodes": self.barcodes,
            "branch_call_number": self.branch_call_number,
            "cat_source": self.cat_source,
            "collection": self.collection,
            "control_number": self.control_number,
            "isbn": self.isbn,
            "oclc_number": self.oclc_number,
            "research_call_number": self.research_call_number,
            "upc": self.upc,
            "update_date": self.update_date,
            "var_fields": self.var_fields,
            "library": self.library,
            "bib_id": self.bib_id,
        }


class BPLSolrResponse(BaseSierraResponse):
    library = "bpl"

    @property
    def barcodes(self) -> list[str]:
        item_data = self._data.get("sm_item_data")
        if not item_data:
            return []
        items = [json.loads(i) for i in item_data if i]
        return [i.get("barcode") for i in items if i and i.get("barcode")]

    @property
    def branch_call_number(self) -> list[str]:
        tag_091 = [i for i in self.var_fields if i["marc_tag"] == "099"]
        call_nos = [" ".join(i["content"] for i in j["subfields"]) for j in tag_091]
        call_nos.append(self._data.get("call_number", ""))
        return list(set([i for i in call_nos if i]))

    @property
    def cat_source(self) -> str:
        cat_source = "vendor"
        tag_001 = self._data.get("ss_marc_tag_001")
        tag_003 = self._data.get("ss_marc_tag_003")
        if tag_001 and tag_001[0] == "o" and tag_003 and tag_003 == "OCoLC":
            cat_source = "inhouse"
        return cat_source

    @property
    def collection(self) -> None:
        return None

    @property
    def control_number(self) -> str | None:
        return self._data.get("ss_marc_tag_001")

    @property
    def isbn(self) -> list[str]:
        isbns = [
            subfield["content"]
            for j in self.var_fields
            if j["marc_tag"] == "020"
            for subfield in j["subfields"]
            if subfield["tag"] == "a"
        ]
        isbns.extend(self._data.get("isbn", []))
        return list(set([i for i in isbns if i]))

    @property
    def oclc_number(self) -> list[str]:
        oclc_nums = [
            subfield["content"]
            for j in self.var_fields
            if j["marc_tag"] == "035"
            for subfield in j["subfields"]
            if subfield["tag"] == "a"
        ]
        oclc_nums.append(self._data.get("ss_marc_tag_001"))
        return list(set([i for i in oclc_nums if i]))

    @property
    def research_call_number(self) -> list[str]:
        return []

    @property
    def upc(self) -> list[str]:
        upcs = [
            subfield["content"]
            for j in self.var_fields
            if j["marc_tag"] in ["024", "028"]
            for subfield in j["subfields"]
            if subfield["tag"] == "a"
        ]
        return list(set([i for i in upcs if i]))

    @property
    def update_date(self) -> str | None:
        return self._data.get("ss_marc_tag_005")

    @property
    def var_fields(self) -> list[dict[str, Any]]:
        var_fields: list[dict[str, Any]] = []
        print(self._data.get("sm_bib_varfields", []))
        for field in self._data.get("sm_bib_varfields", []):
            tag, data = field.split(" || ", 1)
            if "{{" not in data:
                continue
            subfields = [
                {
                    "tag": i.split("}}")[0].strip("{"),
                    "content": i.split("}}")[1].strip(),
                }
                for i in [i for i in data.split(" || ")]
            ]
            var_fields.append({"marc_tag": tag, "subfields": subfields})
        return var_fields


class NYPLPlatformResponse(BaseSierraResponse):
    library = "nypl"

    @property
    def barcodes(self) -> list[str]:
        return []

    @property
    def branch_call_number(self) -> list[str]:
        tag_091 = [i for i in self.var_fields if i["marcTag"] == "091"]
        return [" ".join(i["content"] for i in j["subfields"]) for j in tag_091]

    @property
    def cat_source(self) -> str:
        cat_source = "vendor"
        tag_901_b = [
            subfield["content"]
            for j in self.var_fields
            if j["marcTag"] == "901"
            for subfield in j["subfields"]
            if subfield["tag"] == "b"
        ]
        if any(["CAT" in i for i in tag_901_b]):
            cat_source = "inhouse"
        return cat_source

    @property
    def collection(self) -> str | None:
        collections = [
            subfield["content"]
            for j in self.var_fields
            if j["marcTag"] == "910"
            for subfield in j["subfields"]
            if subfield["tag"] == "a"
        ]
        if len(collections) > 1:
            return "MIXED"
        elif len(collections) == 1:
            return collections[0]
        if self.branch_call_number and self.research_call_number:
            return "MIXED"
        elif self.branch_call_number and not self.research_call_number:
            return "BL"
        elif self.research_call_number and not self.branch_call_number:
            return "RL"
        else:
            return None

    @property
    def control_number(self) -> str | None:
        return self._data.get("controlNumber")

    @property
    def isbn(self) -> list[str]:
        isbns = [
            subfield["content"]
            for j in self.var_fields
            if j["marcTag"] == "020"
            for subfield in j["subfields"]
            if subfield["tag"] == "a"
        ]
        isbns.extend(self._data.get("standardNumbers", []))
        return list(set(isbns))

    @property
    def oclc_number(self) -> list[str]:
        isbns = [
            subfield["content"]
            for j in self.var_fields
            if j["marcTag"] == "035"
            for subfield in j["subfields"]
            if subfield["tag"] == "a"
        ]
        isbns.append(self._data.get("controlNumber"))
        return list(set([i for i in isbns if i]))

    @property
    def research_call_number(self) -> list[str]:
        tag_852 = [
            i for i in self.var_fields if i["marcTag"] == "852" and i["ind1"] == "8"
        ]
        return [" ".join(i["content"] for i in j["subfields"]) for j in tag_852]

    @property
    def upc(self) -> list[str]:
        upcs = [
            subfield["content"]
            for j in self.var_fields
            if j["marcTag"] in ["024", "028"]
            for subfield in j["subfields"]
            if subfield["tag"] == "a"
        ]
        return list(set([i for i in upcs if i]))

    @property
    def update_date(self) -> str | None:
        return self._data.get("updatedDate")

    @property
    def var_fields(self) -> list[dict[str, Any]]:
        return self._data.get("varFields", [])
