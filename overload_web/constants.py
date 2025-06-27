"""Constant values used in the presentation layer of overload_web"""

from __future__ import annotations

from typing import Any, Dict

APPLICATION: str = "Overload"

VENDOR_RULES: Dict[str, Any] = {
    "nypl": {
        "UNKNOWN": {
            "vendor_tags": [],
            "primary_matchpoint": "020",
            "secondary_matchpoint": "001",
        },
        "BT SERIES": {
            "vendor_tags": [{"tag": "901", "code": "a", "value": "BTSERIES"}],
            "primary_matchpoint": "020",
            "secondary_matchpoint": "001",
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
            "vendor_tags": [{"tag": "901", "code": "a", "value": "PARADE"}],
            "primary_matchpoint": "020",
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
            "vendor_tags": [{"tag": "901", "code": "a", "value": "BTROMAN"}],
            "primary_matchpoint": "020",
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
            "vendor_tags": [{"tag": "901", "code": "a", "value": "BTURBN"}],
            "primary_matchpoint": "020",
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
            "vendor_tags": [{"tag": "901", "code": "a", "value": "BTODC"}],
            "primary_matchpoint": "bib_id",
            "secondary_matchpoint": "020",
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
            "vendor_tags": [{"tag": "901", "code": "a", "value": "LEASED"}],
            "primary_matchpoint": "020",
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
            "vendor_tags": [
                {"tag": "901", "code": "a", "value": "Midwest"},
                {"tag": "091", "code": "f", "value": "DVD"},
            ],
            "primary_matchpoint": "001",
            "secondary_matchpoint": "020",
            "tertiary_matchpoint": "024",
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
            "vendor_tags": [
                {"tag": "901", "code": "a", "value": "Midwest"},
                {"tag": "091", "code": "f", "value": "BLURAY"},
            ],
            "primary_matchpoint": "001",
            "secondary_matchpoint": "020",
            "tertiary_matchpoint": "024",
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
            "vendor_tags": [
                {"tag": "901", "code": "a", "value": "Midwest"},
                {"tag": "091", "code": "f", "value": "CD"},
                {"tag": "336", "code": "a", "value": "performed music"},
            ],
            "primary_matchpoint": "001",
            "secondary_matchpoint": "020",
            "tertiary_matchpoint": "024",
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
            "vendor_tags": [
                {"tag": "901", "code": "a", "value": "Midwest"},
                {"tag": "091", "code": "f", "value": "CD"},
                {"tag": "336", "code": "a", "value": "spoken word"},
            ],
            "primary_matchpoint": "001",
            "secondary_matchpoint": "020",
            "tertiary_matchpoint": "024",
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
        "Amalivre": {
            "vendor_tags": [{"tag": "901", "code": "a", "value": "AUXAM"}],
            "primary_matchpoint": "001",
            "secondary_matchpoint": "020",
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
        "Ingram": {
            "vendor_tags": [{"tag": "901", "code": "a", "value": "INGRAM"}],
            "primary_matchpoint": "001",
            "secondary_matchpoint": "020",
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
            "vendor_tags": [{"tag": "037", "code": "b", "value": "Sulaiman"}],
            "primary_matchpoint": "001",
            "secondary_matchpoint": "020",
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
            "vendor_tags": [],
            "primary_matchpoint": "020",
        },
        "Ingram": {
            "vendor_tags": [{"tag": "947", "code": "a", "value": "INGRAM"}],
            "primary_matchpoint": "bib_id",
            "secondary_matchpoint": "020",
            "tertiary_matchpoint": "001",
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
            "vendor_tags": [{"tag": "960", "code": "n", "value": "B&amp;T"}],
            "primary_matchpoint": "bib_id",
            "secondary_matchpoint": "020",
            "tertiary_matchpoint": "022",
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
            "vendor_tags": [{"tag": "037", "code": "b", "value": "B&amp;T SERIES"}],
            "alternate_vendor_tags": [
                {"tag": "947", "code": "a", "value": "B&amp;T SERIES"}
            ],
            "primary_matchpoint": "020",
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
            "vendor_tags": [{"tag": "037", "code": "b", "value": "B&amp;T ROMANCE"}],
            "alternate_vendor_tags": [
                {"tag": "947", "code": "a", "value": "B&amp;T ROMANCE"}
            ],
            "primary_matchpoint": "020",
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
            "vendor_tags": [{"tag": "037", "code": "b", "value": "B&amp;T URBAN"}],
            "alternate_vendor_tags": [
                {"tag": "947", "code": "a", "value": "B&amp;T URBAN"}
            ],
            "primary_matchpoint": "020",
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
            "vendor_tags": [{"tag": "037", "code": "b", "value": "B&amp;T LEASE"}],
            "alternate_vendor_tags": [
                {"tag": "947", "code": "a", "value": "B&amp;T LEASE"}
            ],
            "primary_matchpoint": "020",
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
            "vendor_tags": [{"tag": "037", "code": "b", "value": "B&amp;T PBP"}],
            "alternate_vendor_tags": [
                {"tag": "947", "code": "a", "value": "B&amp;T PBP"}
            ],
            "primary_matchpoint": "020",
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
            "vendor_tags": [
                {"tag": "037", "code": "b", "value": "Midwest"},
                {"tag": "099", "code": "a", "value": "DVD"},
            ],
            "primary_matchpoint": "bib_id",
            "secondary_matchpoint": "020",
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
            "vendor_tags": [
                {"tag": "037", "code": "b", "value": "Midwest"},
                {"tag": "099", "code": "a", "value": "AUDIO"},
            ],
            "primary_matchpoint": "bib_id",
            "secondary_matchpoint": "020",
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
            "vendor_tags": [
                {"tag": "037", "code": "b", "value": "Midwest"},
                {"tag": "099", "code": "a", "value": "CD"},
            ],
            "primary_matchpoint": "bib_id",
            "secondary_matchpoint": "020",
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
