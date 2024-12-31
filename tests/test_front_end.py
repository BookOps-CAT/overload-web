import datetime
import json
import os
from streamlit.testing import v1


def test_streamlit_app():
    at = v1.AppTest.from_file(
        os.path.join(
            os.environ["USERPROFILE"],
            "github/overload-web/overload_web/front_end/pvf.py",
        )
    ).run()
    assert not at.exception


def test_pvf():
    at = v1.AppTest.from_file(
        os.path.join(
            os.environ["USERPROFILE"],
            "github/overload-web/overload_web/front_end/pvf.py",
        )
    ).run()
    assert not at.exception
    assert getattr(at.get("file_uploader")[0], "label") == "Choose a file"
    assert len(at.columns) == 2
    assert at.markdown[0].value == "Process Vendor File"
    assert at.markdown[1].value == "Order Fixed Fields"
    assert at.markdown[2].value == "Order Variable Fields"
    assert at.columns[0].children[1].type == "selectbox"
    assert getattr(at.columns[0].children[1], "label") == "Language"
    assert at.columns[1].children[1].type == "text_input"
    assert getattr(at.columns[1].children[1], "label") == "Internal Note"
    assert at.markdown[3].value == "Sierra Matchpoints"
    assert at.selectbox[5].label == "Primary"
    assert at.selectbox[5].options == ["Sierra ID", "001", "020", "024"]
    assert at.selectbox[6].label == "Secondary"
    assert at.selectbox[6].options == ["Sierra ID", "001", "020", "024"]
    assert at.selectbox[7].label == "Tertiary"
    assert at.selectbox[7].options == ["Sierra ID", "001", "020", "024"]
    assert at.button[0].label == "Process"


def test_pvf_submit_form():
    at = v1.AppTest.from_file(
        os.path.join(
            os.environ["USERPROFILE"],
            "github/overload-web/overload_web/front_end/pvf.py",
        )
    ).run()
    at.selectbox[0].select("a")
    at.text_input[0].input("foo")
    at.text_input[1].input("bar")
    at.text_input[2].input("5.00")
    at.text_input[3].input("10001adbk")
    at.text_input[4].input("5")
    at.selectbox[1].select("a")
    at.date_input[0].set_value(datetime.datetime(2024, 12, 31))
    at.text_input[5].input("evp")
    at.selectbox[2].select("a")
    at.selectbox[3].select("a")
    at.text_input[6].input("baz")
    at.text_input[7].input("foo")
    at.selectbox[4].select("a")
    at.text_input[8].input("bar")
    at.selectbox[5].select("020")
    at.selectbox[6].select("024")
    at.selectbox[7].select("001")
    at.button[0].click().run()
    assert not at.exception
    assert getattr(at.get("file_uploader")[0], "label") == "Choose a file"
    assert json.loads(at.json[0].value) == {
        "order": {},
        "template": {
            "primary_matchpoint": "020",
            "secondary_matchpoint": "024",
            "tertiary_matchpoint": "001",
            "blanket_po": "",
            "vendor_notes": "",
            "internal_note": "",
            "var_field_isbn": "",
            "vendor_title_no": "",
            "language": "a",
            "locations": "foo",
            "shelves": "bar",
            "price": "5.00",
            "fund": "10001adbk",
            "copies": "5",
            "country": "a",
            "create_date": "2024-12-31",
            "vendor_code": "evp",
            "format": "a",
            "selector": "a",
            "audience": "baz",
            "source": "foo",
            "order_type": "a",
            "status": "bar",
        },
    }


def test_pvf_submit_form_mock_post(mock_st_post_response):
    at = v1.AppTest.from_file(
        os.path.join(
            os.environ["USERPROFILE"],
            "github/overload-web/overload_web/front_end/pvf.py",
        )
    ).run()
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
