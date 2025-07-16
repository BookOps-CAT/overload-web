"""Constant values used in the presentation layer of overload_web"""

from __future__ import annotations

from typing import Any, Dict

APPLICATION: str = "Overload"

LANG: Dict[str, str] = {
    "ara": "Arabic",
    "ben": "Bengali",
    "chi": "Chinese",
    "eng": "English",
    "fre": "French",
    "ger": "German",
    "heb": "Hebrew",
    "hin": "Hindi",
    "hun": "Hungarian",
    "ita": "Italian",
    "jpn": "Japanese",
    "kor": "Korean",
    "pan": "Panjabi",
    "pol": "Polish",
    "por": "Portuguese",
    "rus": "Russian",
    "san": "Sanskrit",
    "spa": "Spanish",
    "ukr": "Ukrainian",
    "und": "Undetermined",
    "urd": "Urdu",
    "yid": "Yiddish",
    "zxx": "No linguistic content",
    "hat": "Haitian French Creole",
    "alb": "Albanian",
}

FORMAT: Dict[str, str] = {
    "-": "undefined",
    "b": "book",
    "p": "periodical",
    "s": "serial",
    "m": "microform",
    "c": "score",
    "r": "audio-other",
    "u": "map",
    "t": "videocassette",
    "f": "film",
    "d": "cd-rom",
    "e": "elec access",
    "k": "kit-bk/audio",
    "v": "dvd",
    "w": "music cd",
    "i": "audio book",
    "g": "video game",
    "a": "arch/manusc.",
    "h": "print & photos",
    "l": "large print",
    "j": "realia",
    "q": "ebook",
    "z": "ejournal",
    "y": "bluray",
    "o": "print & electronic",
    "x": "playway",
    "2": "bookpack",
    "3": "streaming media",
    "5": "read-along book",
}

ORDER_TYPE: Dict[str, str] = {
    "-": "undefined",
    "f": "firm order",
    "o": "stand order",
    "i": "item s.o.",
    "a": "approval plan",
    "s": "subscription",
    "l": "lease",
    "g": "gift",
}

SELECTOR: Dict[str, str] = {
    "-": "---",
    "1": "Acquisitions",
    "a": "Jessica",
    "b": "Stephanie",
    "c": "Elisa",
    "d": "Grace",
    "e": "Emily",
    "f": "Nick",
    "g": "Alexandra",
    "j": "Jason",
    "l": "Christopher",
    "m": "Michelle",
    "n": "Andrew",
    "r": "Libbhy",
    "s": "Yolande",
    "w": "Wayne",
}

AUDIENCE: Dict[str, str] = {
    "-": "---",
    "n": "suppress",
    "a": "adult",
    "j": "juvenile",
    "y": "young adult",
}

MATCHPOINT: Dict[str, str] = {
    "isbn": "020",
    "bib_id": "Sierra ID",
    "upc": "024",
    "oclc_number": "001",
}

TEMPLATE_FIXED_FIELDS: list = [
    {"name": "Price", "id": "price"},
    {"name": "Fund", "id": "fund"},
    {"name": "Copies", "id": "copies"},
    {"name": "Vendor Code", "id": "vendor_code"},
    {"name": "Source", "id": "source"},
    {"name": "Status", "id": "status"},
    {"name": "Create Date", "id": "create_date"},
    {
        "name": "Audience",
        "id": "audience",
        "options": {k: f"{k} ({v.title()})" for k, v in AUDIENCE.items()},
    },
    {
        "name": "Order Type",
        "id": "order_type",
        "options": {k: f"{k} ({v.title()})" for k, v in ORDER_TYPE.items()},
    },
    {
        "name": "Format",
        "id": "format",
        "options": {k: f"{k} ({v.title()})" for k, v in FORMAT.items()},
    },
    {
        "name": "Selector",
        "id": "selector",
        "options": {k: f"{k} ({v.title()})" for k, v in SELECTOR.items()},
    },
    {
        "name": "Country",
        "id": "country",
        "options": {"xxu": "United States"},
    },
    {
        "name": "Language",
        "id": "lang",
        "options": {k: f"{k} ({v.title()})" for k, v in LANG.items()},
    },
]

TEMPLATE_VAR_FIELDS: list[dict] = [
    {"name": "Internal Note", "id": "internal_note"},
    {"name": "ISBN", "id": "var_field_isbn"},
    {"name": "Vendor Notes", "id": "vendor_notes"},
    {"name": "Vendor Title Number", "id": "vendor_title_no"},
    {"name": "Blanket PO", "id": "blanket_po"},
]


MATCHPOINTS: list[Dict[str, Any]] = [
    {
        "id": f"{i}",
        "name": i.title(),
        "options": MATCHPOINT,
    }
    for i in ["primary", "secondary", "tertiary"]
]

FIELD_CONSTANTS: Dict[str, Any] = {
    "fixed_fields": TEMPLATE_FIXED_FIELDS,
    "var_fields": TEMPLATE_VAR_FIELDS,
    "matchpoints": MATCHPOINTS,
}


VENDORS: Dict[str, Any] = {
    "unknown": "Unknown",
    "BT": "BT",
    "midwest": "Midwest",
    "amalivre": "Amalivre",
    "ingram": "Ingram",
    "sulaiman": "Sulaiman",
    "eastview": "Eastview",
}
CONTEXT_VALS: list[Dict[str, Any]] = [
    {
        "id": "record_type",
        "name": "Record Type",
        "options": {"full": "Full", "order_level": "Order-Level"},
    },
    {
        "id": "library",
        "name": "Library System",
        "options": {"bpl": "BPL", "nypl": "NYPL"},
    },
    {
        "id": "collection",
        "name": "Collection",
        "options": {"BL": "Branches", "RL": "Research", "None": "None"},
    },
]


VENDOR_RULES: Dict[str, Any] = {
    "nypl": {
        "UNKNOWN": {
            "vendor_tags": {},
            "bib_template": [],
            "template": {
                "matchpoints": {
                    "primary": "isbn",
                    "secondary": "oclc_number",
                }
            },
            "primary": "isbn",
            "secondary": "oclc_number",
        },
        "BT SERIES": {
            "vendor_tags": {"901": {"code": "a", "value": "BTSERIES"}},
            "template": {
                "matchpoints": {
                    "primary": "isbn",
                    "secondary": "oclc_number",
                }
            },
            "primary": "isbn",
            "secondary": "oclc_number",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        },
        "BT PARADE": {
            "vendor_tags": {"901": {"code": "a", "value": "PARADE"}},
            "template": {"matchpoints": {"primary": "isbn"}},
            "primary": "isbn",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        },
        "BT ROMANCE": {
            "vendor_tags": {"901": {"code": "a", "value": "BTROMAN"}},
            "template": {"matchpoints": {"primary": "isbn"}},
            "primary": "isbn",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        },
        "BT URBAN": {
            "vendor_tags": {"901": {"code": "a", "value": "BTURBN"}},
            "template": {"matchpoints": {"primary": "isbn"}},
            "primary": "isbn",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        },
        "BT ODC": {
            "vendor_tags": {"901": {"code": "a", "value": "BTODC"}},
            "template": {
                "matchpoints": {
                    "primary": "bib_id",
                    "secondary": "isbn",
                }
            },
            "primary": "bib_id",
            "secondary": "isbn",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        },
        "BT LEASED": {
            "vendor_tags": {"901": {"code": "a", "value": "LEASED"}},
            "template": {"matchpoints": {"primary": "isbn"}},
            "primary": "isbn",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        },
        "Midwest DVD": {
            "vendor_tags": {
                "901": {"code": "a", "value": "Midwest"},
                "091": {"code": "f", "value": "DVD"},
            },
            "template": {
                "matchpoints": {
                    "primary": "oclc_number",
                    "secondary": "isbn",
                    "tertiary": "upc",
                }
            },
            "primary": "oclc_number",
            "secondary": "isbn",
            "tertiary": "upc",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=v;",
                }
            ],
        },
        "Midwest Blu-ray": {
            "vendor_tags": {
                "901": {"code": "a", "value": "Midwest"},
                "091": {"code": "f", "value": "BLURAY"},
            },
            "template": {
                "matchpoints": {
                    "primary": "oclc_number",
                    "secondary": "isbn",
                    "tertiary": "upc",
                }
            },
            "primary": "oclc_number",
            "secondary": "isbn",
            "tertiary": "upc",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=b;",
                }
            ],
        },
        "Midwest CD": {
            "vendor_tags": {
                "901": {"code": "a", "value": "Midwest"},
                "091": {"code": "f", "value": "CD"},
                "336": {"code": "a", "value": "performed music"},
            },
            "template": {
                "matchpoints": {
                    "primary": "oclc_number",
                    "secondary": "isbn",
                    "tertiary": "upc",
                }
            },
            "primary": "oclc_number",
            "secondary": "isbn",
            "tertiary": "upc",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=y;",
                }
            ],
        },
        "Midwest Audio": {
            "vendor_tags": {
                "901": {"code": "a", "value": "Midwest"},
                "091": {"code": "f", "value": "CD"},
                "336": {"code": "a", "value": "spoken word"},
            },
            "template": {
                "matchpoints": {
                    "primary": "oclc_number",
                    "secondary": "isbn",
                    "tertiary": "upc",
                }
            },
            "primary": "oclc_number",
            "secondary": "isbn",
            "tertiary": "upc",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=u;",
                }
            ],
        },
        "AMALIVRE": {
            "vendor_tags": {"901": {"code": "a", "value": "AUXAM"}},
            "template": {
                "matchpoints": {
                    "primary": "oclc_number",
                    "secondary": "isbn",
                }
            },
            "primary": "oclc_number",
            "secondary": "isbn",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        },
        "INGRAM": {
            "vendor_tags": {"901": {"code": "a", "value": "INGRAM"}},
            "template": {
                "matchpoints": {
                    "primary": "oclc_number",
                    "secondary": "isbn",
                }
            },
            "primary": "oclc_number",
            "secondary": "isbn",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        },
        "Sulaiman": {
            "vendor_tags": {"037": {"code": "b", "value": "Sulaiman"}},
            "template": {
                "matchpoints": {
                    "primary": "oclc_number",
                    "secondary": "isbn",
                }
            },
            "primary": "oclc_number",
            "secondary": "isbn",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                },
                {
                    "tag": "901",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "SULAIMAN",
                },
            ],
        },
    },
    "bpl": {
        "UNKNOWN": {
            "vendor_tags": {},
            "template": {"matchpoints": {"primary": "isbn"}},
            "primary": "isbn",
        },
        "INGRAM": {
            "vendor_tags": {"947": {"code": "a", "value": "INGRAM"}},
            "template": {
                "matchpoints": {
                    "primary": "bib_id",
                    "secondary": "isbn",
                    "tertiary": "oclc_number",
                }
            },
            "primary": "bib_id",
            "secondary": "isbn",
            "tertiary": "oclc_number",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        },
        "BT CLS": {
            "vendor_tags": {"960": {"code": "n", "value": "B&amp;T"}},
            "template": {
                "matchpoints": {
                    "primary": "bib_id",
                    "secondary": "isbn",
                    "tertiary": "022",
                }
            },
            "primary": "bib_id",
            "secondary": "isbn",
            "tertiary": "022",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        },
        "BT SERIES": {
            "vendor_tags": {"037": {"code": "b", "value": "B&amp;T SERIES"}},
            "alternate_vendor_tags": {"947": {"code": "a", "value": "B&amp;T SERIES"}},
            "template": {"matchpoints": {"primary": "isbn"}},
            "primary": "isbn",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        },
        "BT ROMANCE": {
            "vendor_tags": {"037": {"code": "b", "value": "B&amp;T ROMANCE"}},
            "alternate_vendor_tags": {"947": {"code": "a", "value": "B&amp;T ROMANCE"}},
            "template": {"matchpoints": {"primary": "isbn"}},
            "primary": "isbn",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        },
        "BT URBAN": {
            "vendor_tags": {"037": {"code": "b", "value": "B&amp;T URBAN"}},
            "alternate_vendor_tags": {"947": {"code": "a", "value": "B&amp;T URBAN"}},
            "template": {"matchpoints": {"primary": "isbn"}},
            "primary": "isbn",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        },
        "BT LEASE": {
            "vendor_tags": {"037": {"code": "b", "value": "B&amp;T LEASE"}},
            "alternate_vendor_tags": {"947": {"code": "a", "value": "B&amp;T LEASE"}},
            "template": {"matchpoints": {"primary": "isbn"}},
            "primary": "isbn",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        },
        "BT PBP": {
            "vendor_tags": {"037": {"code": "b", "value": "B&amp;T PBP"}},
            "alternate_vendor_tags": {"947": {"code": "a", "value": "B&amp;T PBP"}},
            "template": {"matchpoints": {"primary": "isbn"}},
            "primary": "isbn",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=a;",
                }
            ],
        },
        "Midwest DVD": {
            "vendor_tags": {
                "037": {"code": "b", "value": "Midwest"},
                "099": {"code": "a", "value": "DVD"},
            },
            "template": {
                "matchpoints": {
                    "primary": "bib_id",
                    "secondary": "isbn",
                }
            },
            "primary": "bib_id",
            "secondary": "isbn",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=h;",
                }
            ],
        },
        "Midwest Audio": {
            "vendor_tags": {
                "037": {"code": "b", "value": "Midwest"},
                "099": {"code": "a", "value": "AUDIO"},
            },
            "template": {
                "matchpoints": {
                    "primary": "bib_id",
                    "secondary": "isbn",
                }
            },
            "primary": "bib_id",
            "secondary": "isbn",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=i;",
                }
            ],
        },
        "Midwest CD": {
            "vendor_tags": {
                "037": {"code": "b", "value": "Midwest"},
                "099": {"code": "a", "value": "CD"},
            },
            "template": {
                "matchpoints": {
                    "primary": "bib_id",
                    "secondary": "isbn",
                }
            },
            "primary": "bib_id",
            "secondary": "isbn",
            "bib_template": [
                {
                    "tag": "949",
                    "ind1": "",
                    "ind2": "",
                    "subfield_code": "a",
                    "value": "*b2=j;",
                }
            ],
        },
    },
}


MARC_MAPPING: dict[str, Any] = {
    "907": {"a", "bib_id"},
    "960": {
        "c": "order_code_1",
        "d": "order_code_2",
        "e": "order_code_3",
        "f": "order_code_4",
        "g": "format",
        "i": "order_type",
        "m": "status",
        "o": "copies",
        "q": "create_date",
        "s": "price",
        "t": "locations",
        "u": "fund",
        "v": "vendor_code",
        "w": "lang",
        "x": "country",
        "z": "order_id",
    },
    "961": {
        "d": "internal_note",
        "f": "selector_note",
        "h": "vendor_notes",
        "i": "vendor_title_no",
        "l": "var_field_isbn",
        "m": "blanket_po",
    },
}
