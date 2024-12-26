import json
import os
from streamlit.testing import v1


def test_streamlit_app(streamlit_path):
    at = v1.AppTest.from_file(os.path.join(streamlit_path, "streamlit_app.py")).run()
    assert not at.exception


def test_pvf(streamlit_path, mock_post_response):
    at = v1.AppTest.from_file(os.path.join(streamlit_path, "pvf.py")).run()
    assert not at.exception
    assert len(at.columns) == 2
    assert at.markdown[0].value == "Process Vendor File"
    assert at.text_area[0].label == "Order Data"
    assert at.text_area[1].label == "Template data in JSON"
    assert at.columns[0].children[0].type == "text_area"
    assert getattr(at.columns[0].children[0], "label") == "Order Data"
    assert at.columns[1].children[0].type == "text_area"
    assert getattr(at.columns[1].children[0], "label") == "Template data in JSON"
    assert at.markdown[1].value == "Sierra Matchpoints"
    assert at.selectbox[0].label == "Primary"
    assert at.selectbox[0].options == ["Sierra ID", "001", "020", "024"]
    assert at.selectbox[1].label == "Secondary"
    assert at.selectbox[1].options == ["Sierra ID", "001", "020", "024"]
    assert at.selectbox[2].label == "Tertiary"
    assert at.selectbox[2].options == ["Sierra ID", "001", "020", "024"]
    assert at.button[0].label == "Process"


def test_pvf_submit_form(streamlit_path, mock_post_response):
    at = v1.AppTest.from_file(os.path.join(streamlit_path, "pvf.py")).run()
    at.button[0].click().run()
    assert not at.exception
    assert json.loads(at.json[0].value) == {
        "order": {"library": "nypl"},
        "template": {
            "fund": "foo",
            "primary_matchpoint": "foo",
            "secondary_matchpoint": "bar",
            "tertiary_matchpoint": "baz",
        },
    }
