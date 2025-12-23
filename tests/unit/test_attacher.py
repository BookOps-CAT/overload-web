import json

import pytest

from overload_web.bib_records.domain import bibs, marc_protocols
from overload_web.bib_records.domain_services import (
    attacher,
)
from overload_web.bib_records.infrastructure.sierra import responses, reviewer


class StubFetcher(marc_protocols.BibFetcher):
    def __init__(self) -> None:
        self.session = None


class FakeBibFetcher(StubFetcher):
    def __init__(self, library, collection):
        super().__init__()
        self.library = library
        self.collection = collection

    def get_bibs_by_id(self, value, key):
        if str(self.library) == "nypl":
            file = f"tests/data/{str(self.library)}_{str(self.collection)}.json"
            with open(file, "r", encoding="utf-8") as fh:
                bibs = json.loads(fh.read())
            data = bibs["data"]
            return [responses.NYPLPlatformResponse(data=i) for i in data]
        else:
            file = f"tests/data/{str(self.library)}.json"
            with open(file, "r", encoding="utf-8") as fh:
                bibs = json.loads(fh.read())
            data = bibs["response"]["docs"]
            return [responses.BPLSolrResponse(data=i) for i in data]


def stub_sierra_response(stub_order_bib, library, collection):
    responses = FakeBibFetcher(library=library, collection=collection).get_bibs_by_id(
        key="isbn", value="9781234567890"
    )
    return bibs.MatcherResponse(bib=stub_order_bib, matches=responses)


@pytest.mark.parametrize(
    "library, collection",
    [
        ("nypl", "BL"),
        ("nypl", "RL"),
        ("bpl", "NONE"),
    ],
)
class TestAttacher:
    @pytest.fixture
    def stub_full_response(self, stub_full_bib, library, collection):
        responses = FakeBibFetcher(
            library=library, collection=collection
        ).get_bibs_by_id(key="isbn", value="9781234567890")
        return bibs.MatcherResponse(bib=stub_full_bib, matches=responses)

    @pytest.fixture
    def stub_order_response(self, stub_order_bib, library, collection):
        responses = FakeBibFetcher(
            library=library, collection=collection
        ).get_bibs_by_id(key="isbn", value="9781234567890")
        return bibs.MatcherResponse(bib=stub_order_bib, matches=responses)

    def test_attach_acq(self, library, collection, stub_order_response):
        stub_service = attacher.BibAttacher(
            reviewer=reviewer.ReviewerFactory().make(
                record_type="acq", collection=collection, library=library
            )
        )
        attached_bibs = stub_service.attach([stub_order_response])
        assert attached_bibs[0].bib_id is None
        assert stub_order_response.bib.bib_id is None

    def test_attach_cat(self, library, collection, stub_full_response):
        stub_service = attacher.BibAttacher(
            reviewer=reviewer.ReviewerFactory().make(
                record_type="cat", collection=collection, library=library
            )
        )
        attached_bibs = stub_service.attach([stub_full_response])
        assert attached_bibs[0].bib_id == "123"

    def test_attach_sel(self, library, collection, stub_order_response):
        stub_service = attacher.BibAttacher(
            reviewer=reviewer.ReviewerFactory().make(
                record_type="sel", collection=collection, library=library
            )
        )
        attached_bibs = stub_service.attach([stub_order_response])
        assert attached_bibs[0].bib_id == "123"

    def test_reviewer_factory(self, library, collection):
        with pytest.raises(ValueError) as exc:
            reviewer.ReviewerFactory().make(
                record_type="foo", collection=collection, library=library
            )
        assert str(exc.value) == "Invalid library/record_type/collection combination"
