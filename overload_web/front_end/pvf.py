import datetime
import io
import json
import os
from typing import Any, Dict
import streamlit as st
import requests

from overload_web.front_end.constants import TEMPLATE_FIXED_FIELDS, TEMPLATE_VAR_FIELDS


def process(data: dict) -> dict:
    url = os.environ.get("API_URL_BASE", "http://localhost:8501/pvf")
    if "localhost" not in url:
        response = requests.post(url=url, json=data)
        return response.json()
    else:
        return data


out_data: Dict[str, Any] = {"order": {}, "template": {}}

order_file = st.file_uploader("Choose a file")

if order_file is not None:
    data = io.BytesIO(order_file.getvalue())
    out_data["order"] = json.load(data)

with st.form("process_vendor_file"):
    st.write("Process Vendor File")
    col1, col2 = st.columns(2)
    col1.write("Order Fixed Fields")
    col2.write("Order Variable Fields")
    for k, v in TEMPLATE_FIXED_FIELDS.items():
        if v["type"] == "selectbox":
            out_data["template"][k] = col1.selectbox(v["display"], v["values"])
        elif v["type"] == "text_input":
            out_data["template"][k] = col1.text_input(v["display"])
        elif v["type"] == "date_input":
            date = col1.date_input(v["display"])
            if isinstance(date, datetime.date) or isinstance(date, datetime.datetime):
                out_data["template"][k] = datetime.datetime.strftime(date, "%Y-%m-%d")
    for k, v in TEMPLATE_VAR_FIELDS.items():
        if v["type"] == "text_input":
            out_data["template"][k] = col2.text_input(v["display"])
    st.write("Sierra Matchpoints")
    for m in ["primary", "secondary", "tertiary"]:
        out_data["template"][f"{m}_matchpoint"] = st.selectbox(
            m.title(), ["Sierra ID", "001", "020", "024"]
        )
    submitted = st.form_submit_button("Process")

if submitted:
    st.json(process(out_data))
