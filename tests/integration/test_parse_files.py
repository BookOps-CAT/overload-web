import pytest

from overload_web.domain.pvf import aggregate, services


@pytest.fixture
def make_stub_response():
    def stub_response(library, collection):
        isbns = ["9781234567890"]
        title = "Record 1"
        id = "12345"
        call_no = "Foo"
        control_no = "ocn123456789"
        if library == "bpl":
            return {
                "call_number": call_no,
                "id": id,
                "isbn": isbns,
                "sm_bib_varfields": ["005 || 20200101000001.0", "024 || {{a}} 12345"],
                "sm_item_data": ['{"barcode": "33333123456789"}'],
                "ss_marc_tag_001": control_no,
                "ss_marc_tag_003": "OCoLC",
                "ss_marc_tag_005": "20000101010000.0",
                "title": title,
            }
        if collection == "RL":
            tag = "852"
            ind1 = "8"
        else:
            tag = "091"
            ind1 = " "
        return {
            "id": id,
            "controlNumber": control_no,
            "standardNumbers": isbns,
            "title": title,
            "updatedDate": "2000-01-01T01:00:00",
            "varFields": [
                {
                    "marcTag": tag,
                    "ind1": ind1,
                    "ind2": " ",
                    "subfields": [{"content": call_no, "tag": "a"}],
                },
                {"marcTag": "901", "subfields": [{"content": "CAT", "tag": "b"}]},
                {"marcTag": "910", "subfields": [{"content": collection, "tag": "a"}]},
            ],
        }

    return stub_response


@pytest.fixture
def stub_matcher(fake_fetcher):
    return services.BibMatcher(fetcher=fake_fetcher)


@pytest.fixture
def stub_matcher_no_matches(fake_fetcher, monkeypatch):
    def empty_response(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "overload_web.infrastructure.sierra_clients.SierraBibFetcher.get_bibs_by_id",
        empty_response,
    )
    return services.BibMatcher(fetcher=fake_fetcher)


@pytest.fixture(params=[("nypl", "BL"), ("nypl", "RL"), ("bpl", None)])
def mock_bib(stub_bib, request):
    marker = request.node.get_closest_marker("workflow")
    record_type = marker.kwargs["record_type"]

    return stub_bib(request.param[0], request.param[1], record_type)


@pytest.fixture
def stub_aggregate(stub_bib, request):
    marker = request.node.get_closest_marker("workflow")
    record_type = marker.kwargs["record_type"]
    library = marker.kwargs["library"]
    collection = marker.kwargs["collection"]
    records = [stub_bib(library, collection, record_type)]
    if record_type == "cat":
        job = aggregate.FullRecordJob(workflow_id="1")
        job.records = records
    else:
        job = aggregate.OrderLevelJob(workflow_id="1", vendor="UNKNOWN")
        job.file_records = {"foo.mrc": records}
    return job


@pytest.fixture
def mock_matcher(fake_fetcher, make_stub_response, monkeypatch, request):
    marker = request.node.get_closest_marker("workflow")
    library = marker.kwargs["library"]
    collection = marker.kwargs.get("collection")

    def mock_response(*args, **kwargs):
        return [make_stub_response(library, collection)]

    monkeypatch.setattr(services.BibMatcher, "match_order_record", mock_response)
    monkeypatch.setattr(services.BibMatcher, "match_full_record", mock_response)
    return services.BibMatcher(fetcher=fake_fetcher)


class TestAggregateParseFiles:
    @pytest.mark.workflow(record_type="acq", library="nypl", collection="BL")
    def test_match_records_acq_nypl_bl(self, stub_aggregate, mock_matcher):
        stub_aggregate.match_records(
            matcher=mock_matcher, matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(stub_aggregate.file_records["foo.mrc"]) == 1
        assert stub_aggregate.file_records["foo.mrc"][0].bib_id is None

    @pytest.mark.workflow(record_type="acq", library="nypl", collection="RL")
    def test_match_records_acq_nypl_rl(self, stub_aggregate, mock_matcher):
        stub_aggregate.match_records(
            matcher=mock_matcher, matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(stub_aggregate.file_records["foo.mrc"]) == 1
        assert stub_aggregate.file_records["foo.mrc"][0].bib_id is None

    @pytest.mark.workflow(record_type="acq", library="bpl", collection=None)
    def test_match_records_acq_bpl(self, stub_aggregate, mock_matcher):
        stub_aggregate.match_records(
            matcher=mock_matcher, matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(stub_aggregate.file_records["foo.mrc"]) == 1
        assert stub_aggregate.file_records["foo.mrc"][0].bib_id is None

    @pytest.mark.workflow(record_type="cat", library="nypl", collection="BL")
    def test_match_records_cat_nypl_bl(self, stub_aggregate, mock_matcher):
        stub_aggregate.match_records(matcher=mock_matcher)
        assert len(stub_aggregate.records) == 1
        assert stub_aggregate.records[0].bib_id == "12345"

    @pytest.mark.workflow(record_type="cat", library="nypl", collection="RL")
    def test_match_records_cat_nypl_rl(self, stub_aggregate, mock_matcher):
        stub_aggregate.match_records(matcher=mock_matcher)
        assert len(stub_aggregate.records) == 1
        assert stub_aggregate.records[0].bib_id == "12345"

    @pytest.mark.workflow(record_type="cat", library="bpl", collection=None)
    def test_match_records_cat_bpl(self, stub_aggregate, mock_matcher):
        stub_aggregate.match_records(matcher=mock_matcher)
        assert len(stub_aggregate.records) == 1
        assert stub_aggregate.records[0].bib_id == "12345"

    @pytest.mark.workflow(record_type="sel", library="nypl", collection="BL")
    def test_match_records_sel_nypl_bl(self, stub_aggregate, mock_matcher):
        stub_aggregate.match_records(
            matcher=mock_matcher, matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(stub_aggregate.file_records["foo.mrc"]) == 1
        assert stub_aggregate.file_records["foo.mrc"][0].bib_id == "12345"

    @pytest.mark.workflow(record_type="sel", library="nypl", collection="RL")
    def test_match_records_sel_nypl_rl(self, stub_aggregate, mock_matcher):
        stub_aggregate.match_records(
            matcher=mock_matcher, matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(stub_aggregate.file_records["foo.mrc"]) == 1
        assert stub_aggregate.file_records["foo.mrc"][0].bib_id == "12345"

    @pytest.mark.workflow(record_type="sel", library="bpl", collection=None)
    def test_match_records_sel_bpl(self, stub_aggregate, mock_matcher):
        stub_aggregate.match_records(
            matcher=mock_matcher, matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(stub_aggregate.file_records["foo.mrc"]) == 1
        assert stub_aggregate.file_records["foo.mrc"][0].bib_id == "12345"
