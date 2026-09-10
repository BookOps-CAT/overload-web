import pytest
from sqlmodel import Session, SQLModel, create_engine

from overload_web.application.pvf import marc, update
from overload_web.application.pvf.process import (
    ProcessAcquisitionsRecords,
    ProcessCatalogingRecords,
    ProcessSelectionRecords,
)
from overload_web.domain.pvf import batch
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
def missing_barcodes(monkeypatch):
    def get_barcodes(*args, **kwargs):
        return ["333330987654321"]

    monkeypatch.setattr(batch.BarcodeValidator, "validate_unique", get_barcodes)


@pytest.fixture
def marc_stubs(monkeypatch):
    def bytes_response(*args, **kwargs):
        return b""

    def fake_updates(*args, **kwargs):
        return []

    def null_response(*args, **kwargs):
        pass

    monkeypatch.setattr(marc.BibParser, "combine_marc_files", bytes_response)
    monkeypatch.setattr(marc_handler.MarcReaderWriter, "write", bytes_response)
    monkeypatch.setattr(update.BibUpdater, "get_cat_updates", fake_updates)
    monkeypatch.setattr(update.BibUpdater, "update_record", null_response)


@pytest.fixture(params=[("nypl", "BL"), ("nypl", "RL"), ("bpl", None)])
def mock_marc(monkeypatch, stub_bib, request):
    marker = request.node.get_closest_marker("workflow")
    record_type = marker.kwargs["record_type"]

    def parse_bibs(*args, **kwargs):
        return [stub_bib(request.param[0], request.param[1], record_type)]

    monkeypatch.setattr(marc.BibParser, "parse_marc_data", parse_bibs)


@pytest.fixture(params=[("nypl", "BL"), ("nypl", "RL"), ("bpl", None)])
def mock_marc_dupes(monkeypatch, stub_bib, request):
    marker = request.node.get_closest_marker("workflow")
    record_type = marker.kwargs["record_type"]

    def parse_bibs(*args, **kwargs):
        bib = stub_bib(request.param[0], request.param[1], record_type)
        return [bib, bib]

    monkeypatch.setattr(marc.BibParser, "parse_marc_data", parse_bibs)


class FakeMarcParser:
    def __init__(self) -> None:
        self.library = "foo"
        self.record_type = "bar"
        self.collection = "baz"
        self.bib_mapping: dict = {}
        self.order_mapping: dict = {}
        self.vendor_rules: dict = {}
        self.reader = FakeMarcReader(self.library)


class FakeMarcReader:
    def __init__(self, library: str) -> None:
        self.library = library

    def write(self, records: list) -> bytes:
        return b""


@pytest.mark.usefixtures("marc_stubs")
class TestProcessCommands:
    FAKE_MARC_PARSER = FakeMarcParser()
    FAKE_UPDATE_RULES = {
        "order_mapping": {},
        "default_loc": "foo",
        "bib_id_tag": "bar",
        "library": "baz",
        "record_type": "qux",
        "collection": "spam",
    }
    STUB_ENGINE = marc_handler.MarcUpdateHandler()

    @pytest.mark.workflow(record_type="cat")
    def test_cat_service_process_vendor_file(
        self, fake_fetcher, stub_repo, caplog, mock_marc
    ):
        out = ProcessCatalogingRecords.execute(
            batches={"foo.mrc": b""},
            marc_handler=self.STUB_ENGINE,
            marc_update_rules=self.FAKE_UPDATE_RULES,
            fetcher=fake_fetcher,
            repo=stub_repo,
            marc_parser=self.FAKE_MARC_PARSER,
        )
        assert out["id"] is not None
        assert "Integrity validation: True, missing_barcodes: []" in [
            i.msg for i in caplog.records
        ]

    @pytest.mark.workflow(record_type="cat")
    def test_cat_service_process_vendor_file_missing_barcodes(
        self, fake_fetcher, stub_repo, missing_barcodes, caplog, mock_marc
    ):
        out = ProcessCatalogingRecords.execute(
            batches={"foo.mrc": b""},
            marc_handler=self.STUB_ENGINE,
            marc_update_rules=self.FAKE_UPDATE_RULES,
            fetcher=fake_fetcher,
            repo=stub_repo,
            marc_parser=self.FAKE_MARC_PARSER,
        )
        assert out["id"] is not None
        assert "Integrity validation: False, missing_barcodes: ['333330987654321']" in [
            i.msg for i in caplog.records
        ]
        assert "Barcodes integrity error: ['333330987654321']" in [
            i.msg for i in caplog.records
        ]

    @pytest.mark.workflow(record_type="sel")
    def test_sel_service_process_vendor_file(self, fake_fetcher, stub_repo, mock_marc):
        out = ProcessSelectionRecords.execute(
            {"foo.mrc": b""},
            marc_handler=self.STUB_ENGINE,
            fetcher=fake_fetcher,
            marc_update_rules=self.FAKE_UPDATE_RULES,
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
            repo=stub_repo,
            marc_parser=self.FAKE_MARC_PARSER,
        )
        assert out["id"] is not None

    @pytest.mark.workflow(record_type="acq")
    def test_acq_service_process_vendor_file(self, fake_fetcher, stub_repo, mock_marc):
        out = ProcessAcquisitionsRecords.execute(
            {"foo.mrc": b""},
            marc_handler=self.STUB_ENGINE,
            fetcher=fake_fetcher,
            marc_update_rules=self.FAKE_UPDATE_RULES,
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
            repo=stub_repo,
            marc_parser=self.FAKE_MARC_PARSER,
        )
        assert out["id"] is not None

    @pytest.mark.workflow(record_type="cat")
    def test_cat_service_process_vendor_file_dupes(
        self, fake_fetcher, stub_repo, mock_marc_dupes
    ):
        with pytest.raises(ValueError) as exc:
            ProcessCatalogingRecords.execute(
                batches={"foo.mrc": b""},
                marc_handler=self.STUB_ENGINE,
                fetcher=fake_fetcher,
                marc_update_rules=self.FAKE_UPDATE_RULES,
                repo=stub_repo,
                marc_parser=self.FAKE_MARC_PARSER,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)

    @pytest.mark.workflow(record_type="acq")
    def test_acq_service_process_vendor_file_dupes(
        self, fake_fetcher, stub_repo, mock_marc_dupes
    ):
        with pytest.raises(ValueError) as exc:
            ProcessAcquisitionsRecords.execute(
                {"foo.mrc": b""},
                marc_handler=self.STUB_ENGINE,
                fetcher=fake_fetcher,
                marc_update_rules=self.FAKE_UPDATE_RULES,
                template_data={"format": "a"},
                matchpoints={"primary_matchpoint": "isbn", "vendor": "UNKNOWN"},
                repo=stub_repo,
                marc_parser=self.FAKE_MARC_PARSER,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)

    @pytest.mark.workflow(record_type="sel")
    def test_sel_service_process_vendor_file_dupes(
        self, fake_fetcher, stub_repo, mock_marc_dupes
    ):
        with pytest.raises(ValueError) as exc:
            ProcessSelectionRecords.execute(
                {"foo.mrc": b""},
                marc_handler=self.STUB_ENGINE,
                fetcher=fake_fetcher,
                marc_update_rules=self.FAKE_UPDATE_RULES,
                template_data={"format": "a"},
                matchpoints={"primary_matchpoint": "isbn", "vendor": "UNKNOWN"},
                repo=stub_repo,
                marc_parser=self.FAKE_MARC_PARSER,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)
