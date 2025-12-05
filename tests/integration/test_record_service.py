import copy
import json

import pytest
from bookops_marc import Bib

from overload_web.bib_records.domain import bibs, marc_protocols
from overload_web.bib_records.domain_services import (
    matcher,
    parser,
    serializer,
)
from overload_web.bib_records.infrastructure import marc, sierra, sierra_responses
from overload_web.errors import OverloadError


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
            return [sierra_responses.NYPLPlatformResponse(data=i) for i in data]
        else:
            file = f"tests/data/{str(self.library)}.json"
            with open(file, "r", encoding="utf-8") as fh:
                bibs = json.loads(fh.read())
            data = bibs["response"]["docs"]
            return [sierra_responses.BPLSolrResponse(data=i) for i in data]


@pytest.fixture
def stub_full_bib(make_full_bib):
    dto = make_full_bib({"020": {"code": "a", "value": "9781234567890"}})
    return dto


@pytest.fixture
def stub_order_bib(make_order_bib):
    dto = make_order_bib({"020": {"code": "a", "value": "9781234567890"}})
    return dto


# @pytest.mark.parametrize(
#     "library, collection",
#     [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
# )
# class TestRecordProcessingAttacher:


#     @pytest.fixture
#     def stub_service(self):
#         return attacher.BibAttacher(reviewer=sierra_reviewer.SierraResponseReviewer())

#     @pytest.fixture
#     def stub_full_responses(self, stub_full_bib, library, collection):
#         responses = FakeBibFetcher(library=library, collection=collection).get_bibs_by_id()
#         return bibs.MatcherResponse(bib=stub_full_bib, )

#     def test_attach_cat(self, stub_service, stub_full_bib):
#         matched_bibs = stub_service.attach(
#             [stub_full_bib], record_type=bibs.RecordType.CATALOGING
#         )
#         assert len(matched_bibs[0].matches) == 4

#     def test_attach_cat_no_matches(self, stub_service_no_matches, stub_full_bib):
#         matched_bibs = stub_service_no_matches.attach(
#             [stub_full_bib], record_type=bibs.RecordType.CATALOGING
#         )
#         assert len(matched_bibs[0].matches) == 0

#     def test_attach_cat_no_vendor_index(self, stub_service, stub_order_bib):
#         with pytest.raises(OverloadError) as exc:
#             stub_service.attach([stub_order_bib], record_type=bibs.RecordType.CATALOGING)
#         assert str(exc.value) == "Vendor index required for cataloging workflow."

#     def test_attach_cat_alternate_tags(self, stub_service, make_full_bib):
#         dto = make_full_bib(
#             {
#                 "020": {"code": "a", "value": "9781234567890"},
#                 "947": {"code": "a", "value": "B&amp;T SERIES"},
#             },
#         )
#         matched_bibs = stub_service.attach([dto], record_type=bibs.RecordType.CATALOGING)
#         assert len(matched_bibs[0].matches) == 4

#     @pytest.mark.parametrize(
#         "record_type",
#         [bibs.RecordType.ACQUISITIONS, bibs.RecordType.SELECTION],
#     )
#     def test_match_order_level(self, stub_service, stub_order_bib, record_type):
#         matched_bibs = stub_service.attach(
#             [stub_order_bib],
#             matchpoints={"primary_matchpoint": "isbn"},
#             record_type=record_type,
#         )
#         assert len(matched_bibs[0].matches) == 4

#     @pytest.mark.parametrize(
#         "record_type",
#         [bibs.RecordType.ACQUISITIONS, bibs.RecordType.SELECTION],
#     )
#     def test_match_order_level_no_matches(
#         self, stub_service_no_matches, stub_order_bib, record_type
#     ):
#         matched_bibs = stub_service_no_matches.attach(
#             [stub_order_bib],
#             matchpoints={"primary_matchpoint": "isbn"},
#             record_type=record_type,
#         )
#         assert len(matched_bibs[0].matches) == 0

#     @pytest.mark.parametrize(
#         "record_type",
#         [bibs.RecordType.ACQUISITIONS, bibs.RecordType.SELECTION],
#     )
#     def test_match_order_level_no_matchpoints(
#         self, stub_service, stub_order_bib, record_type
#     ):
#         with pytest.raises(OverloadError) as exc:
#             stub_service.attach([stub_order_bib], record_type=record_type)
#         assert (
#             str(exc.value)
#             == "Matchpoints from order template required for acquisition or selection workflow."
#         )


@pytest.mark.parametrize(
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
class TestRecordProcessingMatcher:
    @pytest.fixture
    def stub_service(self, monkeypatch, library, collection):
        def fake_fetcher(*args, **kwargs):
            return FakeBibFetcher(library, collection)

        monkeypatch.setattr(
            "overload_web.bib_records.infrastructure.sierra.SierraBibFetcher",
            fake_fetcher,
        )
        return matcher.BibMatcher(fetcher=sierra.SierraBibFetcher(library))

    @pytest.fixture
    def stub_service_no_matches(self, monkeypatch, library):
        def fake_fetcher(*args, **kwargs):
            return StubFetcher()

        monkeypatch.setattr(
            "overload_web.bib_records.infrastructure.sierra.SierraBibFetcher",
            fake_fetcher,
        )
        return matcher.BibMatcher(fetcher=sierra.SierraBibFetcher(library))

    def test_match_full(self, stub_service, stub_full_bib):
        matched_bibs = stub_service.match(
            [stub_full_bib], record_type=bibs.RecordType.CATALOGING
        )
        assert len(matched_bibs[0].matches) == 4

    def test_match_full_no_matches(self, stub_service_no_matches, stub_full_bib):
        matched_bibs = stub_service_no_matches.match(
            [stub_full_bib], record_type=bibs.RecordType.CATALOGING
        )
        assert len(matched_bibs[0].matches) == 0

    def test_match_full_no_vendor_index(self, stub_service, stub_order_bib):
        with pytest.raises(OverloadError) as exc:
            stub_service.match([stub_order_bib], record_type=bibs.RecordType.CATALOGING)
        assert str(exc.value) == "Vendor index required for cataloging workflow."

    def test_match_full_alternate_tags(self, stub_service, make_full_bib):
        dto = make_full_bib(
            {
                "020": {"code": "a", "value": "9781234567890"},
                "947": {"code": "a", "value": "B&amp;T SERIES"},
            },
        )
        matched_bibs = stub_service.match([dto], record_type=bibs.RecordType.CATALOGING)
        assert len(matched_bibs[0].matches) == 4

    @pytest.mark.parametrize(
        "record_type",
        [bibs.RecordType.ACQUISITIONS, bibs.RecordType.SELECTION],
    )
    def test_match_order_level(self, stub_service, stub_order_bib, record_type):
        matched_bibs = stub_service.match(
            [stub_order_bib],
            matchpoints={"primary_matchpoint": "isbn"},
            record_type=record_type,
        )
        assert len(matched_bibs[0].matches) == 4

    @pytest.mark.parametrize(
        "record_type",
        [bibs.RecordType.ACQUISITIONS, bibs.RecordType.SELECTION],
    )
    def test_match_order_level_no_matches(
        self, stub_service_no_matches, stub_order_bib, record_type
    ):
        matched_bibs = stub_service_no_matches.match(
            [stub_order_bib],
            matchpoints={"primary_matchpoint": "isbn"},
            record_type=record_type,
        )
        assert len(matched_bibs[0].matches) == 0

    @pytest.mark.parametrize(
        "record_type",
        [bibs.RecordType.ACQUISITIONS, bibs.RecordType.SELECTION],
    )
    def test_match_order_level_no_matchpoints(
        self, stub_service, stub_order_bib, record_type
    ):
        with pytest.raises(OverloadError) as exc:
            stub_service.match([stub_order_bib], record_type=record_type)
        assert (
            str(exc.value)
            == "Matchpoints from order template required for acquisition or selection workflow."
        )


@pytest.mark.parametrize(
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
class TestRecordProcessingSerializer:
    @pytest.fixture
    def stub_service(self, library, stub_constants):
        return serializer.BibSerializer(
            serializer=marc.BookopsMarcUpdater(rules=stub_constants["updater_rules"]),
        )

    def test_update_cat(self, stub_service, stub_full_bib):
        original_bib = Bib(
            copy.deepcopy(stub_full_bib.binary_data), library=str(stub_full_bib.library)
        )
        stub_full_bib.bib_id = "12345"
        updated_bibs = stub_service.update(
            [stub_full_bib], record_type=bibs.RecordType.CATALOGING
        )
        updated_bib = Bib(
            updated_bibs[0].binary_data, library=str(updated_bibs[0].library)
        )
        assert len(original_bib.get_fields("907")) == 0
        assert len(updated_bib.get_fields("907")) == 1

    def test_update_cat_no_vendor_index(self, stub_service, stub_order_bib):
        with pytest.raises(OverloadError) as exc:
            stub_service.update(
                [stub_order_bib], record_type=bibs.RecordType.CATALOGING
            )
        assert str(exc.value) == "Vendor index required for cataloging workflow."

    def test_update_cat_vendor_updates(self, stub_service, make_full_bib, library):
        dto = make_full_bib(
            {
                "020": {"code": "a", "value": "9781234567890"},
                "901": {"code": "a", "value": "INGRAM"},
                "947": {"code": "a", "value": "INGRAM"},
            },
        )
        original_bib = copy.deepcopy(Bib(dto.binary_data, library=library))
        updated_bibs = stub_service.update(
            [dto], record_type=bibs.RecordType.CATALOGING
        )
        assert len(original_bib.get_fields("949")) == 1
        assert (
            len(Bib(updated_bibs[0].binary_data, library=library).get_fields("949"))
            == 2
        )

    def test_update_acq(self, stub_service, stub_order_bib, template_data):
        original_orders = copy.deepcopy(stub_order_bib.orders)
        updated_bibs = stub_service.update(
            [stub_order_bib],
            template_data=template_data,
            record_type=bibs.RecordType.ACQUISITIONS,
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in updated_bibs[0].orders] == ["b"]

    def test_update_sel(self, stub_service, stub_order_bib, template_data):
        original_orders = copy.deepcopy(stub_order_bib.orders)
        updated_bibs = stub_service.update(
            [stub_order_bib],
            template_data=template_data,
            record_type=bibs.RecordType.SELECTION,
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in updated_bibs[0].orders] == ["b"]

    @pytest.mark.parametrize(
        "record_type",
        [bibs.RecordType.ACQUISITIONS, bibs.RecordType.SELECTION],
    )
    def test_update_acq_sel_no_template(
        self, stub_service, stub_order_bib, record_type
    ):
        with pytest.raises(OverloadError) as exc:
            stub_service.update([stub_order_bib], record_type=record_type)
        assert (
            str(exc.value)
            == "Order template required for acquisition or selection workflow."
        )

    def test_serialize(self, stub_order_bib, stub_service, caplog):
        marc_binary = stub_service.serialize(records=[stub_order_bib])
        assert marc_binary.read()[0:2] == b"00"
        assert len(caplog.records) == 1
        assert "Writing MARC binary for record: " in caplog.records[0].msg


@pytest.mark.parametrize(
    "library, collection",
    [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
)
class TestRecordProcessingParser:
    @pytest.fixture
    def stub_service(self, library, stub_constants):
        return parser.BibParser(
            mapper=marc.BookopsMarcMapper(
                rules=stub_constants["mapper_rules"], library=library
            )
        )

    def test_parse_cat(self, stub_service, stub_full_bib, caplog):
        records = stub_service.parse(
            stub_full_bib.binary_data, record_type=bibs.RecordType.CATALOGING
        )
        assert len(records) == 1
        assert str(records[0].library) == str(stub_service.mapper.library)
        assert records[0].isbn == "9781234567890"
        assert str(records[0].library) == str(stub_service.mapper.library)
        assert records[0].barcodes == ["333331234567890"]
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    @pytest.mark.parametrize(
        "record_type",
        [bibs.RecordType.ACQUISITIONS, bibs.RecordType.SELECTION],
    )
    def test_parse_sel_acq(
        self, stub_service, stub_order_bib, record_type, caplog, collection
    ):
        records = stub_service.parse(
            stub_order_bib.binary_data, record_type=record_type
        )
        assert len(records) == 1
        assert str(records[0].library) == str(stub_service.mapper.library)
        assert records[0].isbn == "9781234567890"
        assert str(records[0].collection) == str(collection)
        assert records[0].barcodes == ["333331234567890"]
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg


# @pytest.mark.parametrize(
#     "library, collection",
#     [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")],
# )
# class TestRecordProcessingParser:
#     @pytest.fixture
#     def stub_service(self, library, stub_constants):
#         return parser.BibParser(
#             mapper=marc.BookopsMarcMapper(
#                 rules=stub_constants["mapper_rules"], library=library
#             )
#         )

#     @pytest.mark.parametrize(
#         "record_type",
#         [
#             bibs.RecordType.ACQUISITIONS,
#             bibs.RecordType.CATALOGING,
#             bibs.RecordType.SELECTION,
#         ],
#     )
#     def test_parse(self, stub_constants, library, stub_full_bib, caplog, record_type):
#         parse_service = parser.BibParser(
#             mapper=marc.BookopsMarcMapper(
#                 rules=stub_constants["mapper_rules"],
#                 library=library,
#                 record_type=record_type.value,
#             )
#         )
#         records = parse_service.parse(stub_full_bib.binary_data)
#         assert len(records) == 1
#         assert str(records[0].library) == str(parse_service.mapper.library)
#         assert records[0].isbn == "9781234567890"
#         assert str(records[0].library) == str(parse_service.mapper.library)
#         assert records[0].barcodes == ["333331234567890"]
#         assert len(caplog.records) == 1
#         assert "Vendor record parsed: " in caplog.records[0].msg

#     @pytest.mark.parametrize(
#         "record_type",
#         [bibs.RecordType.ACQUISITIONS, bibs.RecordType.SELECTION],
#     )
#     def test_parse_sel_acq(
#         self, stub_constants, library, stub_order_bib, record_type, caplog
#     ):
#         parse_service = parser.BibParser(
#             mapper=marc.BookopsMarcMapper(
#                 rules=stub_constants["mapper_rules"],
#                 library=library,
#                 record_type=record_type.value,
#             )
#         )
#         records = parse_service.parse(stub_order_bib.binary_data)
#         assert len(records) == 1
#         assert str(records[0].library) == str(parse_service.mapper.library)
#         assert records[0].isbn == "9781234567890"
#         assert str(records[0].library) == str(parse_service.mapper.library)
#         assert records[0].barcodes == ["333331234567890"]
#         assert len(caplog.records) == 1
#         assert "Vendor record parsed: " in caplog.records[0].msg
