"""Domain models that define responses from Sierra"""

from __future__ import annotations

import datetime
import json
import logging
from typing import Any

from overload_web.bib_records.domain import bibs

logger = logging.getLogger(__name__)


class BPLSolrResponse(bibs.BaseSierraResponse):
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
        tag_099 = [i for i in self.var_fields if i["marc_tag"] == "099"]
        call_nos = [" ".join(i["content"] for i in j["subfields"]) for j in tag_099]
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
    def update_date(self) -> str:
        return self._data["ss_marc_tag_005"]

    @property
    def update_datetime(self) -> datetime.datetime:
        return datetime.datetime.strptime(self.update_date, "%Y%m%d%H%M%S.%f")

    @property
    def var_fields(self) -> list[dict[str, Any]]:
        var_fields: list[dict[str, Any]] = []
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


class NYPLPlatformResponse(bibs.BaseSierraResponse):
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
        oclcs = [
            subfield["content"]
            for j in self.var_fields
            if j["marcTag"] == "035"
            for subfield in j["subfields"]
            if subfield["tag"] == "a"
        ]
        oclcs.append(self._data.get("controlNumber"))
        return list(set([i for i in oclcs if i]))

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
    def update_date(self) -> str:
        return self._data["updatedDate"]

    @property
    def update_datetime(self) -> datetime.datetime:
        return datetime.datetime.strptime(self.update_date, "%Y-%m-%dT%H:%M:%S")

    @property
    def var_fields(self) -> list[dict[str, Any]]:
        return self._data.get("varFields", [])
