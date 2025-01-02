import streamlit as st

st.set_page_config(page_title="Overload")

home_page = st.Page("home.py", title="Tools")
get_bib_page = st.Page("get_bib.py", title="Get Bib")
pvf_page = st.Page("pvf.py", title="Process Vendor File")
wc2sierra_page = st.Page("wc2sierra.py", title="Worldcat2Sierra")

pg = st.navigation(
    {"Overload Web": [home_page, get_bib_page, pvf_page, wc2sierra_page]}
)


pg.run()
