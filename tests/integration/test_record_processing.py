import pytest
from sqlmodel import Session, SQLModel, create_engine

from overload_web.application.pvf.process import (
    ProcessAcquisitionsRecords,
    ProcessCatalogingRecords,
    ProcessSelectionRecords,
)
from overload_web.domain.pvf import models
from overload_web.infrastructure import batch_db, marc_handler


@pytest.fixture(scope="class")
def stub_repo():
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield batch_db.PVFBatchRepository(session=session)
    session.close()
    test_engine.dispose()


@pytest.fixture
def update_rules(library, record_type, collection, get_constants):
    constants = get_constants["constants"]
    return {
        "order_mapping": constants["order_mapping"],
        "default_loc": constants["default_locations"][library].get(collection),
        "bib_id_tag": constants["bib_id_tag"][library],
        "library": library,
        "record_type": record_type,
        "collection": collection,
    }


@pytest.fixture
def missing_barcodes(monkeypatch):
    def get_barcodes(*args, **kwargs):
        return ["333330987654321"]

    monkeypatch.setattr(
        "overload_web.domain.pvf.batch.BarcodeValidator.validate_unique", get_barcodes
    )


@pytest.fixture
def stub_bib():
    def make_bib(library, collection, record_type):
        return models.DomainBib(
            library=library,
            collection=collection,
            isbn="9781234567890",
            title="Foo",
            record_type=record_type,
            binary_data=b"",
            branch_call_number="Foo",
            research_call_number=["Foo"],
            barcodes=["333331234567890"],
            orders=[],
            update_date="20200101010000.0",
            vendor_info=models.VendorInfo(
                name="UNKNOWN",
                bib_fields=[],
                matchpoints={
                    "primary_matchpoint": "isbn",
                    "secondary_matchpoint": "control_number",
                },
            ),
            parsed_fields=[],
        )

    return make_bib


@pytest.fixture
def stub_parsed_bib(monkeypatch, stub_bib, record_type, library, collection):
    def parse_bibs(*args, **kwargs):
        bib = stub_bib(library, collection, record_type)
        return [bib]

    monkeypatch.setattr(
        "overload_web.application.pvf.marc.BibParser.parse_marc_data", parse_bibs
    )


@pytest.fixture
def dupe_barcodes(monkeypatch, stub_bib, record_type, library, collection):
    def parse_bibs(*args, **kwargs):
        bib = stub_bib(library, collection, record_type)
        return [bib, bib]

    monkeypatch.setattr(
        "overload_web.application.pvf.marc.BibParser.parse_marc_data", parse_bibs
    )


class TestProcessCommands:
    ENGINE = marc_handler.MarcUpdateHandler()

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_cat_service_process_vendor_file(
        self,
        fake_fetcher,
        stub_repo,
        parsing_handler,
        update_rules,
        caplog,
        stub_parsed_bib,
    ):
        out = ProcessCatalogingRecords.execute(
            batches={"foo.mrc": b""},
            marc_handler=self.ENGINE,
            marc_update_rules=update_rules,
            fetcher=fake_fetcher,
            repo=stub_repo,
            marc_parser=parsing_handler,
        )
        assert out["id"] is not None
        assert "Integrity validation: True, missing_barcodes: []" in [
            i.msg for i in caplog.records
        ]

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_cat_service_process_vendor_file_missing_barcodes(
        self,
        fake_fetcher,
        stub_repo,
        parsing_handler,
        update_rules,
        missing_barcodes,
        caplog,
        stub_parsed_bib,
    ):
        out = ProcessCatalogingRecords.execute(
            batches={"foo.mrc": b""},
            marc_handler=self.ENGINE,
            marc_update_rules=update_rules,
            fetcher=fake_fetcher,
            repo=stub_repo,
            marc_parser=parsing_handler,
        )
        assert out["id"] is not None
        assert "Integrity validation: False, missing_barcodes: ['333330987654321']" in [
            i.msg for i in caplog.records
        ]
        assert "Barcodes integrity error: ['333330987654321']" in [
            i.msg for i in caplog.records
        ]

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
    )
    def test_sel_service_process_vendor_file(
        self, fake_fetcher, stub_repo, parsing_handler, update_rules, stub_parsed_bib
    ):
        out = ProcessSelectionRecords.execute(
            {"foo.mrc": b""},
            marc_handler=self.ENGINE,
            fetcher=fake_fetcher,
            marc_update_rules=update_rules,
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
            repo=stub_repo,
            marc_parser=parsing_handler,
        )
        assert out["id"] is not None

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "acq"), ("nypl", "RL", "acq"), ("bpl", "NONE", "acq")],
    )
    def test_acq_service_process_vendor_file(
        self, fake_fetcher, stub_repo, parsing_handler, update_rules, stub_parsed_bib
    ):
        out = ProcessAcquisitionsRecords.execute(
            {"foo.mrc": b""},
            marc_handler=self.ENGINE,
            fetcher=fake_fetcher,
            marc_update_rules=update_rules,
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
            repo=stub_repo,
            marc_parser=parsing_handler,
        )
        assert out["id"] is not None

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_cat_service_process_vendor_file_dupes(
        self, fake_fetcher, stub_repo, parsing_handler, update_rules, dupe_barcodes
    ):
        with pytest.raises(ValueError) as exc:
            ProcessCatalogingRecords.execute(
                batches={"foo.mrc": b""},
                marc_handler=self.ENGINE,
                fetcher=fake_fetcher,
                marc_update_rules=update_rules,
                repo=stub_repo,
                marc_parser=parsing_handler,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "acq"), ("nypl", "RL", "acq"), ("bpl", "NONE", "acq")],
    )
    def test_acq_service_process_vendor_file_dupes(
        self, fake_fetcher, stub_repo, parsing_handler, update_rules, dupe_barcodes
    ):
        with pytest.raises(ValueError) as exc:
            ProcessAcquisitionsRecords.execute(
                {"foo.mrc": b""},
                marc_handler=self.ENGINE,
                fetcher=fake_fetcher,
                marc_update_rules=update_rules,
                template_data={"format": "a"},
                matchpoints={"primary_matchpoint": "isbn", "vendor": "UNKNOWN"},
                repo=stub_repo,
                marc_parser=parsing_handler,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
    )
    def test_sel_service_process_vendor_file_dupes(
        self, fake_fetcher, stub_repo, parsing_handler, update_rules, dupe_barcodes
    ):
        with pytest.raises(ValueError) as exc:
            ProcessSelectionRecords.execute(
                {"foo.mrc": b""},
                marc_handler=self.ENGINE,
                fetcher=fake_fetcher,
                marc_update_rules=update_rules,
                template_data={"format": "a"},
                matchpoints={"primary_matchpoint": "isbn", "vendor": "UNKNOWN"},
                repo=stub_repo,
                marc_parser=parsing_handler,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)
