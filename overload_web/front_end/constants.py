from typing import Any, Dict

TEMPLATE_FIXED_FIELDS: Dict[str, Any] = {
    "language": {"display": "Language", "type": "selectbox", "values": ["a", "b"]},
    "locations": {"display": "Locations", "type": "text_input"},
    "shelves": {"display": "Shelves", "type": "text_input"},
    "price": {"display": "Price", "type": "text_input"},
    "fund": {"display": "Fund", "type": "text_input"},
    "copies": {"display": "Copies", "type": "text_input"},
    "country": {"display": "Country", "type": "selectbox", "values": ["a", "b"]},
    "create_date": {"display": "Create Date", "type": "date_input"},
    "vendor_code": {"display": "Vendor Code", "type": "text_input"},
    "format": {"display": "Format", "type": "selectbox", "values": ["a", "b"]},
    "selector": {"display": "Selector", "type": "selectbox", "values": ["a", "b"]},
    "audience": {"display": "Audience", "type": "text_input"},
    "source": {"display": "Source", "type": "text_input"},
    "order_type": {"display": "Order Type", "type": "selectbox", "values": ["a", "b"]},
    "status": {"display": "Status", "type": "text_input"},
}
TEMPLATE_VAR_FIELDS: Dict[str, Any] = {
    "internal_note": {"display": "Internal Note", "type": "text_input"},
    "var_field_isbn": {"display": "ISBN", "type": "text_input"},
    "vendor_notes": {"display": "Vendor Notes", "type": "text_input"},
    "vendor_title_no": {"display": "Vendor Title Number", "type": "text_input"},
    "blanket_po": {"display": "Blanket PO", "type": "text_input"},
}
