import random

import pytest
from bookops_marc import Bib
from pymarc import Field, Subfield

from overload_web.application.pvf import review_service
from overload_web.domain import shared
from overload_web.infrastructure import marc_handler


@pytest.fixture
def stub_full_bib(stub_bib):
    def create_bib(library, collection, control_number, item_tag):
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
                    indicators=(field["ind1"], field["ind2"]),
                    subfields=[
                        Subfield(code=i["code"], value=i["value"])
                        for i in field["subfields"]
                    ],
                )
            )
            parsed_fields.append(
                shared.ParsedField(
                    tag=field["tag"],
                    indicators=(field["ind1"], field["ind2"]),
                    subfields=[
                        shared.ParsedSubfield(code=i["code"], value=i["value"])
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
def stub_reviewer():
    return review_service.BibReviewer(handler=marc_handler.MarcUpdater())


class TestBibReviewer:
    def test_dedupe_attach(self, full_bib_949_item, stub_reviewer):
        bib = full_bib_949_item("123456789")
        bib.action = "attach"
        processed = stub_reviewer.deduplicate(records=[bib])
        assert len(processed["NEW"]) == 0
        assert len(processed["DUP"]) == 1
        assert len(processed["DEDUPED"]) == 0

    def test_dedupe_insert(self, full_bib_949_item, stub_reviewer):
        bib = full_bib_949_item("123456789")
        processed = stub_reviewer.deduplicate(records=[bib])
        assert len(processed["NEW"]) == 1
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 0

    def test_dedupe_combine_bibs(self, full_bib_949_item, stub_reviewer):
        bib1 = full_bib_949_item("123456789")
        bib2 = full_bib_949_item("123456789")
        processed = stub_reviewer.deduplicate(records=[bib1, bib2])
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

    def test_dedupe_combine_bpl_bibs(self, full_bib_960_item, stub_reviewer):
        bib1 = full_bib_960_item("123456789")
        bib2 = full_bib_960_item("123456789")
        processed = stub_reviewer.deduplicate(records=[bib1, bib2])
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

    def test_dedupe_other_recs(self, full_bib_949_item, stub_reviewer):
        bib1a = full_bib_949_item("123456789")
        bib1b = full_bib_949_item("123456789")
        bib2 = full_bib_949_item("987654321")
        processed = stub_reviewer.deduplicate(records=[bib1a, bib1b, bib2])
        new_ctrl_nums = [i.control_number for i in processed["NEW"]]
        deduped_ctrl_nums = [i.control_number for i in processed["DEDUPED"]]
        assert len(processed["NEW"]) == 3
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 2
        assert sorted(new_ctrl_nums) == ["123456789", "123456789", "987654321"]
        assert sorted(deduped_ctrl_nums) == ["123456789", "987654321"]

    def test_dedupe_multiple_groups(self, full_bib_949_item, stub_reviewer):
        bib_1a = full_bib_949_item("123456789")
        bib_1b = full_bib_949_item("123456789")
        bib2 = full_bib_949_item(None)
        bib3 = full_bib_949_item(None)
        bib4 = full_bib_949_item("987654321")
        bib4.control_number = "987654321"
        processed = stub_reviewer.deduplicate(
            records=[bib_1a, bib_1b, bib2, bib3, bib4]
        )
        new_ctrl_nums = [i.control_number for i in processed["NEW"]]
        deduped_ctrl_nums = [i.control_number for i in processed["DEDUPED"]]
        assert len(processed["NEW"]) == 5
        assert len(processed["DUP"]) == 0
        assert len(processed["DEDUPED"]) == 4
        assert new_ctrl_nums == ["123456789", "123456789", None, None, "987654321"]
        assert deduped_ctrl_nums == ["123456789", None, None, "987654321"]
