"""Domain models that define responses from Sierra"""

from __future__ import annotations

import datetime
import json
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseSierraResponse(ABC):
    """An abstract domain model that represents bib data returned from Sierra.

    Attributes:
        library:
            The library to whom the record belongs as a str.
        barcodes:
            The list of barcodes associated with a bib record as strings.
        bib_id:
            The record's sierra bib ID as a string.
        branch_call_number:
            The branch call number for the record as a string, if present.
        cat_source:
            The source of cataloging as a string.
        collection:
            The collection to whom the record belongs as a str, if appropriate.
        control_number:
            The record's control number as a string, if present.
        isbn:
            The ISBNs for the title as a list of strings.
        oclc_number:
            OCLC number(s) identifying the record as a list of strings.
        research_call_number:
            The research call number for the record as a list of strings.
        title:
            The title associated with the record as a string.
        upc:
            The UPC number(s) associated with the record as a list of strings.
        update_date:
            The date the record was last updated as a string.
        update_datetime:
            The date the record was last updated as a datetime.datetime object.
        var_fields:
            MARC data fields present in the record as a list of strings.
    """

    library: str

    def __init__(self, data: dict[str, Any]) -> None:
        """
        Initialize a `BaseSierraResponse` object.

        The concrete implementations of this base class will parse the response
        retrieved from Sierra based on the format of the dictionary that is returned.

        Args:
            data: The data retrieved from Sierra as a dictionary.

        """
        self._data = data
        self.bib_id: str = data["id"]
        self.library = self.__class__.library
        self.title: str = data["title"]

    @property
    @abstractmethod
    def barcodes(self) -> list[str]: ...  # pragma: no branch

    @property
    @abstractmethod
    def branch_call_number(self) -> str | None: ...  # pragma: no branch

    @property
    @abstractmethod
    def cat_source(self) -> str: ...  # pragma: no branch

    @property
    @abstractmethod
    def collection(self) -> str | None: ...  # pragma: no branch

    @property
    @abstractmethod
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
    def update_date(self) -> str: ...  # pragma: no branch

    @property
    @abstractmethod
    def update_datetime(self) -> datetime.datetime: ...  # pragma: no branch

    @property
    @abstractmethod
    def var_fields(self) -> list[dict[str, Any]]: ...  # pragma: no branch


class BPLSolrResponse(BaseSierraResponse):
    library = "bpl"

    @property
    def barcodes(self) -> list[str]:
        item_data = self._data.get("sm_item_data", [])
        items = []
        for item in item_data:
            parsed_item = json.loads(item)
            items.append(parsed_item.get("barcode"))
        return items

    @property
    def branch_call_number(self) -> str | None:
        tag_099 = [i for i in self.var_fields if i["marc_tag"] == "099"]
        call_nos = [" ".join(i["content"] for i in j["subfields"]) for j in tag_099]
        call_nos.append(self._data.get("call_number", ""))
        all_call_nos = list(set([i for i in call_nos if i]))
        if all_call_nos:
            return all_call_nos[0]
        return None

    @property
    def cat_source(self) -> str:
        cat_source = "vendor"
        tag_001 = self._data.get("ss_marc_tag_001")
        tag_003 = self._data.get("ss_marc_tag_003")
        if tag_001 and tag_001[0] == "o" and tag_003 and tag_003 == "OCoLC":
            cat_source = "inhouse"
        return cat_source

    @property
    def collection(self) -> str:
        return "NONE"

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


class NYPLPlatformResponse(BaseSierraResponse):
    library = "nypl"

    @property
    def barcodes(self) -> list[str]:
        return []

    @property
    def branch_call_number(self) -> str | None:
        tag_091 = [i for i in self.var_fields if i["marcTag"] == "091"]
        call_no = [" ".join(i["content"] for i in j["subfields"]) for j in tag_091]
        if call_no:
            return call_no[0]
        return None

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
        branch = False
        research = False
        collections = [
            subfield["content"]
            for j in self.var_fields
            if j["marcTag"] == "910"
            for subfield in j["subfields"]
            if subfield["tag"] == "a"
        ]
        if "BL" in collections:
            branch = True
        if "RL" in collections:
            research = True
        if self.branch_call_number:
            branch = True
        if self.research_call_number:
            research = True
        locations = [i.get("code") for i in self._data.get("locations", [])]
        for loc in locations:
            if len(loc) < 3:
                continue
            if loc == "zzzzz":
                branch = True
            elif loc == "xxx":
                research = True
            elif loc in ["myd", "myh", "mym", "myt"]:
                research = True
            elif loc[:2] == "my" and loc not in ["myd", "myh", "mym", "myt"]:
                branch = True
            elif loc[:2] == "sc":
                research = True
            elif loc[:3] == "maj":
                branch = True
            elif loc[:2] == "ma" and loc[:3] != "maj":
                research = True
            elif loc[:3] in ["lsx", "lsd"]:
                research = True
            elif loc[:2] in NYPL_BRANCHES.keys():
                branch = True
        if branch and research:
            return "MIXED"
        elif branch and not research:
            return "BL"
        elif research and not branch:
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


NYPL_BRANCHES = {
    "ag": "Aguilar",
    "al": "Allerton",
    "ba": "Baychester",
    "bc": "Bronx Library Center",
    "be": "Belmont",
    "bl": "Bloomingdale",
    "br": "George Bruce",
    "bt": "Battery Park",
    "ca": "Cathedral, T. C. Cooke",
    "cc": "SASB",
    "ch": "Chatham Square",
    "ci": "City Island",
    "cl": "Morningside Heights",
    "cn": "Charleston",
    "cp": "Clason's Point",
    "cs": "Columbus",
    "ct": "Castle Hill",
    "dh": "Dongan Hills",
    "dy": "Spuyten Duyvil",
    "ea": "Eastchester",
    "ep": "Epiphany",
    "ew": "Edenwald",
    "fe": "58th Street",
    "fw": "Fort Washington",
    "fx": "Francis Martin",
    "gc": "Grand Central",
    "gd": "Grand Concourse",
    "gk": "Great Kills",
    "hb": "High Bridge",
    "hd": "125th Street",
    "hf": "Hamilton Fish Park",
    "hg": "Hamilton Grange",
    "hk": "Huguenot Park",
    "hl": "Harlem",
    "hp": "Hudson Park",
    "hs": "Hunt's Point",
    "ht": "Countee Cullen",
    "hu": "115th Street (temp)",
    "in": "Inwood",
    "jm": "Jefferson Market",
    "jp": "Jerome Park",
    "kb": "Kingsbridge",
    "kp": "Kips Bay",
    "lb": "Andrew Heiskell",
    "lm": "New Amsterdam",
    "ma": "S.A. Schwarzman Bldg.",
    "mb": "Macomb's Bridge",
    "me": "Melrose",
    "mh": "Mott Haven",
    "ml": "Mulberry Street",
    "mm": "Mid-Manhattan",
    "mn": "Mariner's Harbor",
    "mo": "Mosholu",
    "mp": "Morris Park",
    "mr": "Morrisania",
    "mu": "Muhlenberg",
    "my": "Performing Arts",
    "nb": "West New Brighton",
    "nd": "New Dorp",
    "ns": "96th Street",
    "ot": "Ottendorfer",
    "pk": "Parkchester",
    "pm": "Pelham Bay",
    "pr": "Port Richmond",
    "rd": "Riverdale",
    "ri": "Roosevelt Island",
    "rs": "Riverside",
    "rt": "Richmondtown",
    "sa": "St. Agnes",
    "sb": "South Beach",
    "sc": "Schomburg",
    "sd": "Sedgwick",
    "se": "Seward Park",
    "sg": "St. George Library Center",
    "sl": "Science, Industry & Business",
    "sn": "Stavros Niarcos Library",
    "ss": "67th Street",
    "st": "Stapleton",
    "sv": "Soundview",
    "tg": "Throg's Neck",
    "th": "Todt Hill-Westerleigh",
    "tm": "Tremont",
    "ts": "Tompkins Square",
    "tv": "Tottenville",
    "vc": "Van Cortlandt",
    "vn": "Van Nest",
    "wb": "Webster",
    "wf": "West Farms",
    "wh": "Washington Heights",
    "wk": "Wakefield",
    "wl": "Woodlawn Heights",
    "wo": "Woodstock",
    "wt": "Westchester Square",
    "yv": "Yorkville",
    "ft": "53rd Street",
    "ls": "Library Services Center",
}

BPL_BRANCHES = {
    "02": "Central Juv Children's Room",
    "03": "Central YA Young Teens",
    "04": "Central BKLYN Collection",
    "11": "Central AMMS Art & Music",
    "12": "Central Pop Audiovisual (Multimedia)",
    "13": "Central HBR (Hist/Biog/Rel)",
    "14": "Central Literature & Languages",
    "16": "Central SST",
    "21": "Arlington",
    "22": "Bedford",
    "23": "Business Library",
    "24": "Brighton Beach",
    "25": "Borough Park",
    "26": "Stone Avenue",
    "27": "Brownsville",
    "28": "Bay Ridge",
    "29": "Bushwick",
    "30": "Crown Heights",
    "31": "Carroll Gardens",
    "32": "Coney Island",
    "33": "Clarendon",
    "34": "Canarsie",
    "35": "DeKalb",
    "36": "East Flatbush",
    "37": "Eastern Parkway",
    "38": "Flatbush",
    "39": "Flatlands",
    "40": "Fort Hamilton",
    "41": "Greenpoint",
    "42": "Highlawn",
    "43": "Kensington",
    "44": "Kings Bay",
    "45": "Kings Highway",
    "46": "Leonard",
    "47": "Macon",
    "48": "Midwood",
    "49": "Mapleton",
    "50": "Brooklyn Heights",
    "51": "New Utrecht",
    "52": "New Lots",
    "53": "Park Slope",
    "54": "Rugby",
    "55": "Sunset Park",
    "56": "Sheepshead Bay",
    "57": "Saratoga",
    "59": "Marcy",
    "60": "Williamsburgh",
    "61": "Washington Irving",
    "62": "Walt Whitman",
    "63": "Kidsmobile",
    "64": "BiblioBus",
    "65": "Cypress Hills",
    "66": "Gerritsen Beach",
    "67": "McKinley Park",
    "68": "Mill Basin",
    "69": "Pacific",
    "70": "Red Hook",
    "71": "Ulmer Park",
    "72": "Bookmobile",
    "73": "Bookmobile #2",
    "74": "Gravesend",
    "76": "Homecrest",
    "77": "Windsor Terrace",
    "78": "Paerdegat",
    "79": "Brower Park",
    "80": "Ryder",
    "81": "Jamaica Bay",
    "82": "Dyker",
    "83": "Clinton Hill",
    "84": "Brookdale Pop-up",
    "85": "Spring Creek",
    "87": "Cortelyou",
    "88": "Adams St.",
    "89": "BookOps",
    "90": "Service to the Aging SAGE/SOA",
    "91": "Center for Bkln History",
    "94": "Central Literacy",
}
