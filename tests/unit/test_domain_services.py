import copy
import datetime
import random

import pytest
from bookops_marc import Bib
from pymarc import Field, Indicators, Subfield

from overload_web.domain.pvf import models, services
from overload_web.infrastructure import marc_handler


@pytest.fixture
def create_marc_record():
    def create_marc(library, collection):
        bib = Bib()
        bib.leader = "00000cam  2200517 i 4500"
        bib.library = library
        bib.add_field(Field(tag="005", data="20000101010001.0"))
        bib.add_field(
            Field(
                tag="020",
                indicators=Indicators(" ", " "),
                subfields=[Subfield(code="a", value="9781234567890")],
            )
        )
        if library == "bpl":
            bib.add_field(
                Field(
                    tag="037",
                    indicators=Indicators(" ", " "),
                    subfields=[
                        Subfield(code="a", value="123"),
                        Subfield(code="b", value="OverDrive, Inc."),
                    ],
                )
            )
            bib.add_field(
                Field(
                    tag="099",
                    indicators=Indicators(" ", " "),
                    subfields=[Subfield(code="a", value="Foo")],
                )
            )
        else:
            if collection == "BL":
                bib.add_field(
                    Field(
                        tag="091",
                        indicators=Indicators(" ", " "),
                        subfields=[Subfield(code="a", value="Foo")],
                    )
                )
            else:
                bib.add_field(
                    Field(
                        tag="852",
                        indicators=Indicators("8", " "),
                        subfields=[Subfield(code="a", value="Foo")],
                    )
                )
            bib.add_field(
                Field(
                    tag="910",
                    indicators=Indicators(" ", " "),
                    subfields=[Subfield(code="a", value=collection)],
                )
            )
        bib.add_field(
            Field(
                tag="949",
                indicators=Indicators(" ", "1"),
                subfields=[Subfield(code="i", value="333331234567890")],
            )
        )
        bib.add_field(
            Field(
                tag="960",
                indicators=Indicators(" ", " "),
                subfields=[
                    Subfield(code="a", value="l"),
                    Subfield(code="b", value="-"),
                    Subfield(code="c", value="j"),
                    Subfield(code="d", value="c"),
                    Subfield(code="e", value="d"),
                    Subfield(code="f", value="a"),
                    Subfield(code="g", value="b"),
                    Subfield(code="h", value="-"),
                    Subfield(code="i", value="l"),
                    Subfield(code="j", value="-"),
                    Subfield(code="k", value="A01"),
                    Subfield(code="m", value="o"),
                    Subfield(code="n", value="-"),
                    Subfield(code="o", value="13"),
                    Subfield(code="p", value="  -  -  "),
                    Subfield(code="q", value="01-01-25"),
                    Subfield(code="r", value="  -  -  "),
                    Subfield(code="s", value="{{dollar}}13.20"),
                    Subfield(code="t", value="agj0y"),
                    Subfield(code="u", value="lease"),
                    Subfield(code="v", value="btlea"),
                    Subfield(code="w", value="eng"),
                    Subfield(code="x", value="xxu"),
                    Subfield(code="y", value="1"),
                    Subfield(code="z", value=".o10000010"),
                ],
            )
        )
        bib.add_field(
            Field(
                tag="961",
                indicators=Indicators(" ", " "),
                subfields=[
                    Subfield(code="d", value="foo"),
                    Subfield(code="f", value="bar"),
                    Subfield(code="m", value="baz"),
                ],
            )
        )
        return bib

    return create_marc


@pytest.fixture(params=[("nypl", "BL"), ("nypl", "RL"), ("bpl", None)])
def mock_marc(request, create_marc_record) -> Bib:
    return create_marc_record(request.param[0], request.param[1])


@pytest.fixture
def stub_full_bib(stub_bib):
    def create_bib(library, collection, control_number, item_tag) -> models.DomainBib:
        number = random.randint(0, 100)
        barcode = f"33333{str(number).zfill(10)}"
        if item_tag == "960":
            field_037b = "Foo"
            item_ind2 = " "
        else:
            field_037b = "OverDrive, Inc."
            item_ind2 = "1"
        field_list = [
            {
                "tag": "037",
                "ind1": " ",
                "ind2": " ",
                "subfields": [
                    {"code": "a", "value": "123"},
                    {"code": "b", "value": field_037b},
                ],
            },
            {
                "tag": item_tag,
                "ind1": " ",
                "ind2": item_ind2,
                "subfields": [{"code": "i", "value": barcode}],
            },
            {
                "tag": "949",
                "ind1": " ",
                "ind2": " ",
                "subfields": [{"code": "a", "value": "*b2=a;"}],
            },
        ]
        parsed_fields = []
        bib = Bib()
        bib.leader = "00000cam  2200517 i 4500"
        bib.library = library
        for field in field_list:
            bib.add_field(
                Field(
                    tag=field["tag"],
                    indicators=Indicators(field["ind1"], field["ind2"]),
                    subfields=[
                        Subfield(code=i["code"], value=i["value"])
                        for i in field["subfields"]
                    ],
                )
            )
            parsed_fields.append(
                models.ParsedField(
                    tag=field["tag"],
                    indicators=(field["ind1"], field["ind2"]),
                    subfields=[
                        models.ParsedSubfield(code=i["code"], value=i["value"])
                        for i in field["subfields"]
                    ],
                )
            )
        domain_bib = stub_bib(library, collection, "cat")
        domain_bib.binary_data = bib.as_marc()
        domain_bib.parsed_fields = parsed_fields
        domain_bib.barcodes = [barcode]
        domain_bib.control_number = control_number
        domain_bib.action = "insert"
        return domain_bib

    return create_bib


@pytest.fixture
def stub_domain_bib(request, stub_bib):
    marker = request.node.get_closest_marker("workflow")

    def make_bib(record_type) -> models.DomainBib:
        bib = stub_bib(
            marker.kwargs["library"], marker.kwargs["collection"], record_type
        )
        bib.parsed_fields = [
            models.ParsedField(tag="005", value="20200101010000.0"),
            models.ParsedField(
                tag="020",
                indicators=(" ", " "),
                subfields=[models.ParsedSubfield(code="i", value="9781234567890")],
            ),
            models.ParsedField(
                tag="949",
                indicators=(" ", "1"),
                subfields=[models.ParsedSubfield(code="i", value="333331234567890")],
            ),
        ]
        bib.orders = [
            models.Order(
                locations=["agj0y"],
                audience=["j"],
                branches=["ag"],
                copies="13",
                create_date="01-01-25",
                format="b",
                lang="eng",
                order_id=".o10000010",
                shelves=["0y"],
                status="o",
                vendor_notes=None,
                order_code_1="j",
                order_code_2="c",
                order_code_3="d",
                order_code_4="a",
                order_type="l",
                price="{{dollar}}13.20",
                project_code="A01",
                fund="lease",
                vendor_code="btlea",
                country="xxu",
                internal_note="foo",
                selector_note="bar",
                vendor_title_no=None,
                blanket_po="baz",
            )
        ]
        return bib

    return make_bib


@pytest.fixture(params=[("nypl", "BL"), ("nypl", "RL"), ("bpl", None)])
def full_bib_949_item(stub_full_bib, request):
    def create_bib(control_number):
        return stub_full_bib(request.param[0], request.param[1], control_number, "949")

    return create_bib


@pytest.fixture
def full_bib_960_item(stub_full_bib):
    def create_bib(control_number):
        return stub_full_bib("bpl", None, control_number, "960")

    return create_bib


@pytest.fixture
def stub_updater(request, get_constants):
    marker = request.node.get_closest_marker("workflow")
    collection = marker.kwargs["collection"]
    library = marker.kwargs["library"]
    record_type = marker.kwargs["record_type"]
    constants = get_constants["constants"]
    return services.BibUpdater(
        library=library,
        default_loc=constants["default_locations"][library].get(collection),
        bib_id_tag=constants["bib_id_tag"][library],
        order_mapping=constants["order_mapping"],
        handler=marc_handler.MarcUpdater(),
        record_type=record_type,
        collection=collection,
    )


@pytest.fixture(params=[("nypl", "BL"), ("nypl", "RL"), ("bpl", None)])
def mock_bib(stub_bib, request):
    marker = request.node.get_closest_marker("workflow")
    record_type = marker.kwargs["record_type"]

    return stub_bib(request.param[0], request.param[1], record_type)


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


class TestBarcodeValidator:
    VALIDATOR = services.BarcodeValidator()

    def test_validate_unique(self):
        validated = self.VALIDATOR.validate_unique(
            barcodes=[
                ["333331234567890", "333330987654321"],
                ["333331111111111", "333332222222222"],
            ]
        )
        assert sorted(validated) == sorted(
            ["333331234567890", "333330987654321", "333331111111111", "333332222222222"]
        )

    def test_validate_unique_dupes(self):
        with pytest.raises(ValueError) as exc:
            self.VALIDATOR.validate_unique(
                barcodes=[
                    ["333331234567890", "333330987654321"],
                    ["333331111111111", "333331111111111"],
                ]
            )
        assert str(exc.value) == "Duplicate barcodes found in file: ['333331111111111']"

    def test_validate_preserved(self):
        missing = self.VALIDATOR.validate_preserved(
            processed_barcodes=[
                ["333331234567890", "333330987654321"],
                ["333331111111111", "333332222222222"],
            ],
            original_barcodes=[
                "333331234567890",
                "333330987654321",
                "333331111111111",
                "333332222222222",
            ],
        )
        assert missing == []

    def test_validate_preserved_missing(self, caplog):
        caplog.set_level("DEBUG")
        missing = self.VALIDATOR.validate_preserved(
            processed_barcodes=[
                ["333331234567890", "333330987654321"],
                ["333331111111111"],
            ],
            original_barcodes=[
                "333331234567890",
                "333330987654321",
                "333331111111111",
                "333332222222222",
            ],
        )
        assert missing == ["333332222222222"]
        assert [i.msg for i in caplog.records] == [
            "Integrity validation: False, missing_barcodes: ['333332222222222']",
            "Barcodes integrity error: ['333332222222222']",
        ]


class TestBibMatcher:
    @pytest.mark.workflow(record_type="cat")
    def test_match_full(self, mock_bib, stub_matcher):
        candidates = stub_matcher.match_full_record(mock_bib)
        assert len(candidates) == 1

    @pytest.mark.workflow(record_type="cat")
    def test_match_full_no_candidates(self, stub_matcher_no_matches, mock_bib):
        candidates = stub_matcher_no_matches.match_full_record(mock_bib)
        assert len(candidates) == 0

    @pytest.mark.workflow(record_type="cat")
    def test_match_full_no_vendor_index(self, mock_bib, stub_matcher):
        mock_bib.vendor_info = None
        with pytest.raises(ValueError) as exc:
            stub_matcher.match_full_record(mock_bib)
        assert str(exc.value) == "Vendor index required for cataloging workflow."

    @pytest.mark.workflow(record_type="acq")
    def test_match_order_level(self, mock_bib, stub_matcher):
        candidates = stub_matcher.match_order_record(
            record=mock_bib, matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(candidates) == 1

    @pytest.mark.workflow(record_type="acq")
    def test_match_order_level_no_matches(self, mock_bib, stub_matcher_no_matches):
        candidates = stub_matcher_no_matches.match_order_record(
            record=mock_bib, matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(candidates) == 0

    @pytest.mark.workflow(record_type="acq")
    def test_match_order_level_matchpoint_none(self, mock_bib, stub_matcher):
        candidates = stub_matcher.match_order_record(
            record=mock_bib, matchpoints={"primary_matchpoint": None}
        )
        assert len(candidates) == 0

    @pytest.mark.workflow(record_type="acq")
    def test_match_order_level_no_matchpoints(self, mock_bib, stub_matcher):
        with pytest.raises(TypeError) as exc:
            stub_matcher.match_order_record(record=mock_bib)
        assert (
            str(exc.value)
            == "BibMatcher.match_order_record() missing 1 required positional argument: 'matchpoints'"
        )


class TestBibParser:
    ENGINE = marc_handler.MarcParser()

    @pytest.mark.workflow(record_type="cat")
    def test_combine_marc_files(self, mock_marc, get_constants, request):
        rules = get_constants["parsing_rules"]
        marker = request.node.get_closest_marker("workflow")
        record_type = marker.kwargs["record_type"]
        parser = services.BibParser(
            bib_mapping=rules["bib_mapping"],
            library=mock_marc.library,
            collection=mock_marc.collection,
            record_type=record_type,
            order_mapping=rules["order_mapping"],
            vendor_mapping=rules["vendor_mapping"],
            handler=self.ENGINE,
        )
        combined = parser.combine_marc_files(data=[mock_marc.as_marc()])
        assert len([i for i in combined]) > 1

    @pytest.mark.workflow(record_type="sel")
    def test_parse_marc_data_order_level_record(
        self, mock_marc, get_constants, request, caplog
    ):
        rules = get_constants["parsing_rules"]
        marker = request.node.get_closest_marker("workflow")
        record_type = marker.kwargs["record_type"]
        parser = services.BibParser(
            bib_mapping=rules["bib_mapping"],
            library=mock_marc.library,
            collection=mock_marc.collection,
            record_type=record_type,
            order_mapping=rules["order_mapping"],
            vendor_mapping=rules["vendor_mapping"],
            handler=self.ENGINE,
        )
        records = parser.parse_marc_data(data=mock_marc.as_marc())
        assert len(records) == 1
        assert records[0].library == mock_marc.library
        assert records[0].record_type == record_type
        assert records[0].vendor_info is None
        assert records[0].vendor == "UNKNOWN"
        assert records[0].update_date == "20000101010001.0"
        assert records[0].update_datetime == datetime.datetime(2000, 1, 1, 1, 0, 1, 0)
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    @pytest.mark.workflow(record_type="cat")
    def test_parse_marc_data_cat_record(
        self, mock_marc, get_constants, request, caplog
    ):
        rules = get_constants["parsing_rules"]
        marker = request.node.get_closest_marker("workflow")
        record_type = marker.kwargs["record_type"]
        parser = services.BibParser(
            bib_mapping=rules["bib_mapping"],
            library=mock_marc.library,
            collection=mock_marc.collection,
            record_type=record_type,
            order_mapping=rules["order_mapping"],
            vendor_mapping=rules["vendor_mapping"],
            handler=self.ENGINE,
        )
        records = parser.parse_marc_data(data=mock_marc.as_marc())
        assert len(records) == 1
        assert records[0].library == mock_marc.library
        assert records[0].record_type == record_type
        assert records[0].vendor_info.name == "UNKNOWN"
        assert records[0].update_date == "20000101010001.0"
        assert records[0].update_datetime == datetime.datetime(2000, 1, 1, 1, 0, 1, 0)
        assert len(caplog.records) == 1
        assert "Vendor record parsed: " in caplog.records[0].msg

    @pytest.mark.workflow(library="nypl", collection="BL", record_type="acq")
    def test_write(self, get_constants, stub_domain_bib):
        record = stub_domain_bib("acq")
        rules = get_constants["parsing_rules"]
        parser = services.BibParser(
            bib_mapping=rules["bib_mapping"],
            library=record.library,
            collection=record.collection,
            record_type="acq",
            order_mapping=rules["order_mapping"],
            vendor_mapping=rules["vendor_mapping"],
            handler=self.ENGINE,
        )
        out = parser.write(records=[record])
        assert isinstance(out, bytes)


class TestBibReviewer:
    REVIEWER = services.BibReviewer(handler=marc_handler.MarcUpdater())

    def test_dedupe_attach(self, full_bib_949_item):
        bib = full_bib_949_item("123456789")
        bib.action = "attach"
        reviewed = self.REVIEWER.review_batch(records=[bib])
        processed = self.REVIEWER.deduplicate(reviewed)
        assert len(processed["NEW"]) == 0
        assert len(processed["DUP"]) == 1
        assert len(processed["DEDUPED"]) == 0

    def test_dedupe_insert(self, full_bib_949_item):
        bib = full_bib_949_item("123456789")
        reviewed = self.REVIEWER.review_batch(records=[bib])
        processed = self.REVIEWER.deduplicate(reviewed)
        assert len(processed["NEW"]) == 1
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 0

    def test_dedupe_combine_bibs(self, full_bib_949_item):
        bib1 = full_bib_949_item("123456789")
        bib2 = full_bib_949_item("123456789")
        reviewed = self.REVIEWER.review_batch(records=[bib1, bib2])
        processed = self.REVIEWER.deduplicate(reviewed)
        combined_rec = processed["DEDUPED"][0]
        deduped = Bib(combined_rec.binary_data, library=combined_rec.library)
        new_ctrl_nums = [i.control_number for i in processed["NEW"]]
        deduped_ctrl_nums = [i.control_number for i in processed["DEDUPED"]]
        assert len(processed["NEW"]) == 2
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 1
        assert sorted([i.value() for i in deduped.get_fields("949")]) == [
            "*b2=a;"
        ] + sorted(bib1.barcodes + bib2.barcodes)
        assert new_ctrl_nums == ["123456789", "123456789"]
        assert deduped_ctrl_nums == ["123456789"]

    def test_dedupe_combine_bpl_bibs(self, full_bib_960_item):
        bib1 = full_bib_960_item("123456789")
        bib2 = full_bib_960_item("123456789")
        reviewed = self.REVIEWER.review_batch(records=[bib1, bib2])
        processed = self.REVIEWER.deduplicate(reviewed)
        combined_rec = processed["DEDUPED"][0]
        deduped = Bib(combined_rec.binary_data, library=combined_rec.library)
        new_ctrl_nums = [i.control_number for i in processed["NEW"]]
        deduped_ctrl_nums = [i.control_number for i in processed["DEDUPED"]]
        assert len(processed["NEW"]) == 2
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 1
        assert [i.value() for i in deduped.get_fields("949")] == ["*b2=a;"]
        assert sorted([i.value() for i in deduped.get_fields("960")]) == sorted(
            bib1.barcodes + bib2.barcodes
        )
        assert new_ctrl_nums == ["123456789", "123456789"]
        assert deduped_ctrl_nums == ["123456789"]

    def test_dedupe_other_recs(self, full_bib_949_item):
        bib1a = full_bib_949_item("123456789")
        bib1b = full_bib_949_item("123456789")
        bib2 = full_bib_949_item("987654321")
        reviewed = self.REVIEWER.review_batch(records=[bib1a, bib1b, bib2])
        processed = self.REVIEWER.deduplicate(reviewed)
        new_ctrl_nums = [i.control_number for i in processed["NEW"]]
        deduped_ctrl_nums = [i.control_number for i in processed["DEDUPED"]]
        assert len(processed["NEW"]) == 3
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 2
        assert sorted(new_ctrl_nums) == ["123456789", "123456789", "987654321"]
        assert sorted(deduped_ctrl_nums) == ["123456789", "987654321"]

    def test_dedupe_multiple_groups(self, full_bib_949_item):
        bib_1a = full_bib_949_item("123456789")
        bib_1b = full_bib_949_item("123456789")
        bib2 = full_bib_949_item(None)
        bib3 = full_bib_949_item(None)
        bib4 = full_bib_949_item("987654321")
        bib4.control_number = "987654321"
        reviewed = self.REVIEWER.review_batch(
            records=[bib_1a, bib_1b, bib2, bib3, bib4]
        )
        processed = self.REVIEWER.deduplicate(reviewed)
        new_ctrl_nums = [i.control_number for i in processed["NEW"]]
        deduped_ctrl_nums = [i.control_number for i in processed["DEDUPED"]]
        assert len(processed["NEW"]) == 5
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 4
        assert new_ctrl_nums == ["123456789", "123456789", None, None, "987654321"]
        assert deduped_ctrl_nums == ["123456789", None, None, "987654321"]


class TestBibUpdaterBPL:
    @pytest.mark.workflow(library="bpl", collection=None, record_type="acq")
    def test_get_order_level_updates_acq(self, stub_updater, stub_domain_bib):
        acq_bib = stub_domain_bib("acq")
        original_orders = copy.deepcopy(acq_bib.orders)
        updates = stub_updater.get_order_level_updates(
            record=acq_bib,
            template_data={"name": "Foo", "order_code_1": "b", "format": "a"},
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in acq_bib.orders] == ["b"]
        assert len(updates) == 2
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"

    @pytest.mark.workflow(library="bpl", collection=None, record_type="sel")
    def test_get_order_level_updates_sel(self, stub_updater, stub_domain_bib):
        sel_bib = stub_domain_bib("sel")
        original_orders = copy.deepcopy(sel_bib.orders)
        updates = stub_updater.get_order_level_updates(
            record=sel_bib, template_data={"order_code_1": "b", "format": "a"}
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in sel_bib.orders] == ["b"]
        assert len(updates) == 3
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "949"
        assert updates[2].subfields == [{"code": "a", "value": "*b2=a;"}]
        assert updates[2].target_field_to_delete is None

    @pytest.mark.workflow(library="bpl", collection=None, record_type="sel")
    def test_get_order_level_updates_sel_with_command_tag(
        self, stub_updater, stub_domain_bib
    ):
        sel_bib = stub_domain_bib("sel")
        sel_bib.parsed_fields = [
            models.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[models.ParsedSubfield(code="a", value="*b2=a;")],
            )
        ]
        updates = stub_updater.get_order_level_updates(
            record=sel_bib, template_data={"format": "a"}
        )
        assert len(updates) == 2
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"

    @pytest.mark.workflow(library="bpl", collection=None, record_type="sel")
    def test_get_order_level_updates_sel_no_command_tag(
        self, stub_updater, stub_domain_bib
    ):
        sel_bib = stub_domain_bib("sel")
        updates = stub_updater.get_order_level_updates(record=sel_bib, template_data={})
        assert len(updates) == 2
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"

    @pytest.mark.workflow(library="bpl", collection=None, record_type="cat")
    def test_get_full_record_updates(self, stub_updater, stub_domain_bib):
        cat_bib = stub_domain_bib("cat")
        cat_bib.bib_id = "12345"
        cat_bib.vendor_info = models.VendorInfo(
            name="INGRAM",
            matchpoints={},
            vendor_tags=[],
            bib_fields=[
                {"tag": "949", "ind1": " ", "ind2": " ", "code": "a", "value": "*b2=a;"}
            ],
        )
        updates = stub_updater.get_full_record_updates(record=cat_bib)
        assert len(updates) == 2
        assert updates[0].__dict__ == {
            "tag": "949",
            "delete_fields_by_tag": False,
            "target_field_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "*b2=a;"}],
        }
        assert updates[1].__dict__ == {
            "tag": "907",
            "delete_fields_by_tag": True,
            "target_field_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "12345"}],
        }


class TestBibUpdaterNYPLBranch:
    @pytest.mark.workflow(library="nypl", collection="BL", record_type="acq")
    def test_get_order_level_updates_acq(self, stub_updater, stub_domain_bib):
        acq_bib = stub_domain_bib("acq")
        original_orders = copy.deepcopy(acq_bib.orders)
        updates = stub_updater.get_order_level_updates(
            record=acq_bib,
            template_data={"name": "Foo", "order_code_1": "b", "format": "a"},
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in acq_bib.orders] == ["b"]
        assert len(updates) == 3
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].__dict__ == {
            "tag": "910",
            "delete_fields_by_tag": True,
            "target_field_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "BL"}],
        }

    @pytest.mark.parametrize(
        "template, command_tag",
        [
            ({"order_code_1": "b", "format": "a"}, "*b2=a;bn=zzzzz;"),
            ({"order_code_1": "b"}, "*bn=zzzzz;"),
        ],
    )
    @pytest.mark.workflow(library="nypl", collection="BL", record_type="sel")
    def test_get_order_level_updates_sel(
        self, stub_updater, stub_domain_bib, template, command_tag
    ):
        sel_bib = stub_domain_bib("sel")
        sel_bib.parsed_fields = [
            models.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[models.ParsedSubfield(code="a", value="b2=a")],
            )
        ]
        original_orders = copy.deepcopy(sel_bib.orders)
        updates = stub_updater.get_order_level_updates(
            record=sel_bib, template_data=template
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in sel_bib.orders] == ["b"]
        assert len(updates) == 4
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "949"
        assert updates[2].subfields == [{"code": "a", "value": command_tag}]
        assert updates[2].target_field_to_delete is None
        assert updates[3].tag == "910"

    @pytest.mark.parametrize(
        "original, output",
        [("*b2=a;", "*b2=a;bn=zzzzz;"), ("*b2=a", "*b2=a;bn=zzzzz;")],
    )
    @pytest.mark.workflow(library="nypl", collection="BL", record_type="sel")
    def test_get_order_level_updates_sel_check_command_tag(
        self, stub_updater, stub_domain_bib, original, output
    ):
        sel_bib = stub_domain_bib("sel")
        sel_bib.parsed_fields = [
            models.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[models.ParsedSubfield(code="a", value=original)],
            )
        ]
        updates = stub_updater.get_order_level_updates(
            record=sel_bib, template_data={"order_code_1": "b", "format": "a"}
        )
        assert len(updates) == 4
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "949"
        assert updates[2].subfields == [{"code": "a", "value": output}]
        assert updates[2].target_field_to_delete.__dict__ == {
            "tag": "949",
            "indicators": (" ", " "),
            "code": "a",
            "value": original,
        }
        assert updates[3].tag == "910"

    @pytest.mark.workflow(library="nypl", collection="BL", record_type="sel")
    def test_get_order_level_updates_sel_skip_command_tag(
        self, stub_updater, stub_domain_bib
    ):
        sel_bib = stub_domain_bib("sel")
        sel_bib.parsed_fields = [
            models.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[models.ParsedSubfield(code="a", value="*b2=a;bn=zzzzz;")],
            )
        ]
        updates = stub_updater.get_order_level_updates(
            record=sel_bib, template_data={"order_code_1": "b", "format": "a"}
        )
        assert len(updates) == 3
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "910"

    @pytest.mark.workflow(library="nypl", collection="BL", record_type="cat")
    def test_get_full_record_updates(self, stub_updater, stub_domain_bib):
        cat_bib = stub_domain_bib("cat")
        cat_bib.bib_id = "12345"
        cat_bib.vendor_info = models.VendorInfo(
            name="INGRAM",
            matchpoints={},
            vendor_tags=[],
            bib_fields=[
                {"tag": "949", "ind1": " ", "ind2": " ", "code": "a", "value": "*b2=a;"}
            ],
        )
        updates = stub_updater.get_full_record_updates(record=cat_bib)
        assert len(updates) == 3
        assert updates[0].__dict__ == {
            "tag": "949",
            "delete_fields_by_tag": False,
            "target_field_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "*b2=a;"}],
        }
        assert updates[1].__dict__ == {
            "tag": "945",
            "delete_fields_by_tag": True,
            "target_field_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "12345"}],
        }
        assert updates[2].tag == "910"

    @pytest.mark.parametrize(
        "input,output",
        [
            ({"p": "J", "a": "FIC", "c": "FOO"}, {"p": "J", "a": "FIC", "c": "FOO"}),
            (
                {"p": "J", "f": "HOLIDAY", "a": "PIC", "c": "BAR"},
                {"p": "J", "f": "HOLIDAY", "a": "PIC", "c": "BAR"},
            ),
            (
                {"p": "J", "f": "YR", "a": "FIC", "c": "BAZ"},
                {"p": "J", "f": "YR", "a": "FIC", "c": "BAZ"},
            ),
            (
                {"p": "J SPA", "a": "PIC", "c": "J"},
                {"p": "J SPA", "a": "PIC", "c": "J"},
            ),
            (
                {"f": "GRAPHIC", "a": "FIC", "c": "FOO"},
                {"f": "GRAPHIC", "a": "FIC", "c": "FOO"},
            ),
            ({"p": "J E FOO BAR"}, {"p": "J", "a": "E", "c": "FOO BAR"}),
            ({"p": "J SPA E FOO BAR"}, {"p": "J SPA", "a": "E", "c": "FOO BAR"}),
            (
                {"p": "J", "f": "GRAPHIC", "a": "GN FIC", "c": "BAZ"},
                {"p": "J", "f": "GRAPHIC", "a": "GN FIC", "c": "BAZ"},
            ),
            ({"f": "DVD", "a": "MOVIE", "c": "BAZ"}, {"c": "DVD MOVIE BAZ"}),
        ],
    )
    @pytest.mark.workflow(library="nypl", collection="BL", record_type="cat")
    def test_get_full_record_updates_bt_series_call_no(
        self, stub_updater, stub_domain_bib, input, output
    ):
        cat_bib = stub_domain_bib("cat")
        cat_bib.vendor = "BT SERIES"
        cat_bib.branch_call_number = " ".join([i for i in input.values()])
        updates = stub_updater.get_full_record_updates(record=cat_bib)
        assert len(updates) == 2
        assert updates[0].tag == "910"
        assert updates[1].tag == "091"
        assert updates[1].ind1 == " "
        assert updates[1].ind2 == " "
        assert updates[1].delete_fields_by_tag is True
        assert updates[1].target_field_to_delete is None
        assert updates[1].subfields == [
            {"code": k, "value": v} for k, v in output.items()
        ]

    @pytest.mark.workflow(library="nypl", collection="BL", record_type="cat")
    def test_get_full_record_updates_bt_series_call_no_error(
        self, stub_domain_bib, stub_updater
    ):
        cat_bib = stub_domain_bib("cat")
        cat_bib.vendor = "BT SERIES"
        cat_bib.branch_call_number = "FOO J FIC SNICKET"
        with pytest.raises(ValueError) as exc:
            stub_updater.get_full_record_updates(record=cat_bib)
        assert (
            str(exc.value)
            == "Constructed call number does not match original. New=FIC SNICKET, Original=FOO J FIC SNICKET"
        )


class TestBibUpdaterNYPLResearch:
    @pytest.mark.workflow(library="nypl", collection="RL", record_type="acq")
    def test_get_order_level_updates_acq(self, stub_updater, stub_domain_bib):
        acq_bib = stub_domain_bib("acq")
        original_orders = copy.deepcopy(acq_bib.orders)
        updates = stub_updater.get_order_level_updates(
            record=acq_bib,
            template_data={"name": "Foo", "order_code_1": "b", "format": "a"},
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in acq_bib.orders] == ["b"]
        assert len(updates) == 3
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].__dict__ == {
            "tag": "910",
            "delete_fields_by_tag": True,
            "target_field_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "RL"}],
        }

    @pytest.mark.parametrize(
        "template, command_tag",
        [
            ({"order_code_1": "b", "format": "a"}, "*b2=a;bn=xxx;"),
            ({"order_code_1": "b"}, "*bn=xxx;"),
        ],
    )
    @pytest.mark.workflow(library="nypl", collection="RL", record_type="sel")
    def test_get_order_level_updates_sel(
        self, stub_updater, stub_domain_bib, template, command_tag
    ):
        sel_bib = stub_domain_bib("sel")
        sel_bib.parsed_fields = [
            models.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[models.ParsedSubfield(code="a", value="b2=a")],
            )
        ]
        original_orders = copy.deepcopy(sel_bib.orders)
        updates = stub_updater.get_order_level_updates(
            record=sel_bib, template_data=template
        )
        assert [i.order_code_1 for i in original_orders] == ["j"]
        assert [i.order_code_1 for i in sel_bib.orders] == ["b"]
        assert len(updates) == 4
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "949"
        assert updates[2].subfields == [{"code": "a", "value": command_tag}]
        assert updates[2].target_field_to_delete is None
        assert updates[3].tag == "910"

    @pytest.mark.parametrize(
        "original, output", [("*b2=a;", "*b2=a;bn=xxx;"), ("*b2=a", "*b2=a;bn=xxx;")]
    )
    @pytest.mark.workflow(library="nypl", collection="RL", record_type="sel")
    def test_get_order_level_updates_sel_check_command_tag(
        self, stub_updater, stub_domain_bib, original, output
    ):
        sel_bib = stub_domain_bib("sel")
        sel_bib.parsed_fields = [
            models.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[models.ParsedSubfield(code="a", value=original)],
            )
        ]
        updates = stub_updater.get_order_level_updates(
            record=sel_bib, template_data={"order_code_1": "b", "format": "a"}
        )
        assert len(updates) == 4
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "949"
        assert updates[2].subfields == [{"code": "a", "value": output}]
        assert updates[2].target_field_to_delete.__dict__ == {
            "tag": "949",
            "indicators": (" ", " "),
            "code": "a",
            "value": original,
        }

        assert updates[3].tag == "910"

    @pytest.mark.workflow(library="nypl", collection="RL", record_type="sel")
    def test_get_order_level_updates_sel_skip_command_tag(
        self, stub_updater, stub_domain_bib
    ):
        sel_bib = stub_domain_bib("sel")
        sel_bib.parsed_fields = [
            models.ParsedField(
                tag="949",
                indicators=(" ", " "),
                subfields=[models.ParsedSubfield(code="a", value="*b2=a;bn=xxx;")],
            )
        ]
        updates = stub_updater.get_order_level_updates(
            record=sel_bib, template_data={"order_code_1": "b", "format": "a"}
        )
        assert len(updates) == 3
        assert updates[0].tag == "960"
        assert updates[1].tag == "961"
        assert updates[2].tag == "910"

    @pytest.mark.workflow(library="nypl", collection="RL", record_type="cat")
    def test_get_full_record_updates(self, stub_updater, stub_domain_bib):
        cat_bib = stub_domain_bib("cat")
        cat_bib.bib_id = "12345"
        cat_bib.vendor_info = models.VendorInfo(
            name="INGRAM",
            matchpoints={},
            vendor_tags=[],
            bib_fields=[
                {"tag": "949", "ind1": " ", "ind2": " ", "code": "a", "value": "*b2=a;"}
            ],
        )
        updates = stub_updater.get_full_record_updates(record=cat_bib)
        assert len(updates) == 3
        assert updates[0].__dict__ == {
            "tag": "949",
            "delete_fields_by_tag": False,
            "target_field_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "*b2=a;"}],
        }
        assert updates[1].__dict__ == {
            "tag": "945",
            "delete_fields_by_tag": True,
            "target_field_to_delete": None,
            "ind1": " ",
            "ind2": " ",
            "subfields": [{"code": "a", "value": "12345"}],
        }
        assert updates[2].tag == "910"
