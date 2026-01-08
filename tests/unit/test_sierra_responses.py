import pytest

from overload_web.bib_records.domain_models import sierra_responses


class TestSierraResponses:
    BASE_RESPONSE = {"id": "1234567890", "title": "Foo"}

    def test_nypl_response_bl(self):
        data = {
            "varFields": [
                {
                    "marcTag": "091",
                    "subfields": [
                        {"tag": "a", "content": "FIC"},
                        {"tag": "c", "content": "BAR"},
                    ],
                },
                {
                    "marcTag": "901",
                    "subfields": [{"tag": "b", "content": "CATBL"}],
                },
                {
                    "marcTag": "910",
                    "subfields": [{"tag": "a", "content": "BL"}],
                },
                {
                    "marcTag": "020",
                    "subfields": [{"tag": "a", "content": "9781234567890"}],
                },
                {
                    "marcTag": "024",
                    "subfields": [{"tag": "a", "content": "12345"}],
                },
                {
                    "marcTag": "028",
                    "subfields": [{"tag": "a", "content": "67890"}],
                },
            ],
            "standardNumbers": ["9781234567890"],
            "controlNumber": "on9876543210",
            "updatedDate": "2020-01-01T00:00:01",
            **self.BASE_RESPONSE,
        }
        response = sierra_responses.NYPLPlatformResponse(data)
        assert response.cat_source == "inhouse"
        assert response.collection == "BL"

    def test_nypl_response_rl(self):
        data = {
            "varFields": [
                {
                    "marcTag": "852",
                    "ind1": "8",
                    "subfields": [{"tag": "a", "content": "ReCAP 20-123456"}],
                },
                {
                    "marcTag": "910",
                    "subfields": [{"tag": "a", "content": "RL"}],
                },
            ],
            **self.BASE_RESPONSE,
        }
        response = sierra_responses.NYPLPlatformResponse(data)
        assert response.cat_source == "vendor"
        assert response.collection == "RL"

    def test_nypl_response_mixed(self):
        data = {
            "varFields": [
                {
                    "marcTag": "910",
                    "subfields": [{"tag": "a", "content": "RL"}],
                },
                {
                    "marcTag": "910",
                    "subfields": [{"tag": "a", "content": "BL"}],
                },
            ],
            **self.BASE_RESPONSE,
        }
        response = sierra_responses.NYPLPlatformResponse(data)
        assert response.cat_source == "vendor"
        assert response.collection == "MIXED"

    def test_nypl_response_no_collection(self):
        response = sierra_responses.NYPLPlatformResponse(self.BASE_RESPONSE)
        assert response.collection is None

    @pytest.mark.parametrize(
        "field, collection",
        [({"marcTag": "091"}, "BL"), ({"marcTag": "852", "ind1": "8"}, "RL")],
    )
    def test_nypl_response_call_number_check(self, field, collection):
        field["subfields"] = [{"tag": "a", "content": "Foo"}]
        data = {"varFields": [field], **self.BASE_RESPONSE}
        response = sierra_responses.NYPLPlatformResponse(data)
        assert response.collection == collection

    def test_nypl_response_call_number_mixed(self):
        data = {
            "varFields": [
                {
                    "marcTag": "852",
                    "ind1": "8",
                    "subfields": [{"tag": "a", "content": "ReCAP 20-123456"}],
                },
                {"marcTag": "091", "subfields": [{"tag": "a", "content": "FIC"}]},
            ],
            **self.BASE_RESPONSE,
        }
        response = sierra_responses.NYPLPlatformResponse(data)
        assert response.collection == "MIXED"

    def test_bpl_response(self):
        data = {
            "sm_item_data": ['{"barcode": "333331234567890"}'],
            "ss_marc_tag_001": "on9876543210",
            "ss_marc_tag_003": "OCoLC",
            "ss_marc_tag_005": "20200101000001.0",
            "sm_bib_varfields": [
                "005 || 20200101000001.0",
                "020 || {{a}} 9781234567890",
                "024 || {{a}} 12345",
                "028 || {{a}} 67890",
                "035 || {{a}} (OCoLC)9876543210",
                "099 || {{a}} FIC || {{a}} BAR",
            ],
            "isbn": ["9781234567890"],
            "call_number": "FIC BAR",
            **self.BASE_RESPONSE,
        }
        response = sierra_responses.BPLSolrResponse(data=data)
        assert response.barcodes == ["333331234567890"]
        assert response.branch_call_number == "FIC BAR"
        assert response.cat_source == "inhouse"
        assert len(response.var_fields) == 5

    def test_bpl_response_vendor(self):
        data = {
            "ss_marc_tag_001": "on9876543210",
            "ss_marc_tag_005": "20200101000001.0",
            "sm_bib_varfields": [
                "005 || 20200101000001.0",
                "020 || {{a}} 9781234567890",
                "024 || {{a}} 12345",
                "028 || {{a}} 67890",
                "035 || {{a}} (OCoLC)9876543210",
                "099 || {{a}} FIC || {{a}} BAR",
            ],
            "isbn": ["9781234567890"],
            "call_number": "FIC BAR",
            **self.BASE_RESPONSE,
        }
        response = sierra_responses.BPLSolrResponse(data=data)
        assert response.barcodes == []
        assert response.branch_call_number == "FIC BAR"
        assert response.cat_source == "vendor"
