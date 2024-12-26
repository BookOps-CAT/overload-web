import streamlit as st
import requests

option = st.selectbox("What tool would you like to use?", ("Process Vendor File"))

st.write("")
st.write("Type input below:")
bib_id = st.text_input("Bib ID")

if st.button("Attach"):
    response = requests.get(url=f"http://127.0.0.1:8000/attach/{bib_id}")
    st.subheader(f"Response from API = {response.text}")
