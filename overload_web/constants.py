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
        "values": {k: f"{k} ({v.title()})" for k, v in AUDIENCE.items()},
    },
    {
        "name": "Order Type",
        "id": "order_type",
        "values": {k: f"{k} ({v.title()})" for k, v in ORDER_TYPE.items()},
    },
    {
        "name": "Format",
        "id": "format",
        "values": {k: f"{k} ({v.title()})" for k, v in FORMAT.items()},
    },
    {
        "name": "Selector",
        "id": "selector",
        "values": {k: f"{k} ({v.title()})" for k, v in SELECTOR.items()},
    },
    {
        "name": "Country",
        "id": "country",
        "values": {"xxu": "United States"},
    },
    {
        "name": "Language",
        "id": "lang",
        "values": {k: f"{k} ({v.title()})" for k, v in LANG.items()},
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
        "id": f"{i}_matchpoint",
        "name": i.title(),
        "values": MATCHPOINT,
    }
    for i in ["primary", "secondary", "tertiary"]
]

FIELD_CONSTANTS: Dict[str, Any] = {
    "fixed_fields": TEMPLATE_FIXED_FIELDS,
    "var_fields": TEMPLATE_VAR_FIELDS,
    "matchpoints": MATCHPOINTS,
}
