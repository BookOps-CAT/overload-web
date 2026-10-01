import pytest
from sqlmodel import SQLModel, create_engine

from overload_web.application.pvf.process import (
    ProcessAcquisitionsRecords,
    ProcessCatalogingRecords,
    ProcessSelectionRecords,
)
from overload_web.domain.pvf import match_service, parsing_service, update_service
from overload_web.infrastructure import file_io, marc_handler, unit_of_work


@pytest.fixture(scope="class")
def stub_uow():
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    yield unit_of_work.SqlModelUnitOfWork(engine=test_engine)
    test_engine.dispose()


@pytest.fixture
def missing_barcodes(monkeypatch):
    def get_barcodes(*args, **kwargs):
        return ["333330987654321"]

    monkeypatch.setattr(
        parsing_service.BarcodeValidator, "validate_unique", get_barcodes
    )


@pytest.fixture
def marc_stubs(monkeypatch, mocker, tmp_path):
    def bytes_response(*args, **kwargs):
        return b""

    def fake_updates(*args, **kwargs):
        return []

    def null_response(*args, **kwargs):
        pass

    def fake_file_reference(*args, **kwargs):
        return [{"filename": "foo.mrc", "reference": "bar"}]

    def fake_path(*args, **kwargs):
        return tmp_path / "uploads"

    mock_read = mocker.mock_open(read_data=b"")
    mocker.patch("overload_web.infrastructure.file_io.open", mock_read)
    monkeypatch.setattr("pathlib.Path.mkdir", fake_path)
    monkeypatch.setattr(parsing_service.BibParser, "combine_marc_files", bytes_response)
    monkeypatch.setattr(marc_handler.MarcParser, "write", bytes_response)
    monkeypatch.setattr(update_service.BibUpdater, "get_cat_updates", fake_updates)
    monkeypatch.setattr(update_service.BibUpdater, "apply_field_updates", null_response)
    monkeypatch.setattr(
        file_io.IncomingFileRepository, "list_by_id", fake_file_reference
    )


@pytest.fixture(params=[("nypl", "BL"), ("nypl", "RL"), ("bpl", None)])
def mock_marc(monkeypatch, stub_bib, request):
    marker = request.node.get_closest_marker("workflow")
    record_type = marker.kwargs["record_type"]

    def parse_bibs(*args, **kwargs):
        return [stub_bib(request.param[0], request.param[1], record_type)]

    monkeypatch.setattr(parsing_service.BibParser, "parse_marc_data", parse_bibs)


@pytest.fixture(params=[("nypl", "BL"), ("nypl", "RL"), ("bpl", None)])
def mock_marc_dupes(monkeypatch, stub_bib, request):
    marker = request.node.get_closest_marker("workflow")
    record_type = marker.kwargs["record_type"]

    def parse_bibs(*args, **kwargs):
        bib = stub_bib(request.param[0], request.param[1], record_type)
        return [bib, bib]

    monkeypatch.setattr(parsing_service.BibParser, "parse_marc_data", parse_bibs)


@pytest.fixture
def stub_update_service():
    return update_service.BibUpdater(
        handler=marc_handler.MarcUpdater(),
        order_mapping={},
        default_loc="foo",
        bib_id_tag="bar",
        library="baz",
    )


@pytest.fixture
def stub_parsing_service():
    return parsing_service.BibParser(
        handler=FakeMarcParser(),
        library="foo",
        record_type="bar",
        collection="baz",
        vendor_mapping={},
        bib_mapping={},
        order_mapping={},
    )


@pytest.fixture
def fake_matcher(fake_fetcher):
    return match_service.BibMatcher(fetcher=fake_fetcher)


class FakeMarcParser:
    def __init__(self) -> None:
        self.library = "foo"
        self.record_type = "bar"
        self.collection = "baz"
        self.bib_mapping: dict = {}
        self.order_mapping: dict = {}
        self.vendor_mapping: dict = {}

    def write(self, records: list) -> bytes:
        return b""


@pytest.mark.usefixtures("marc_stubs")
class TestProcessCommands:
    @pytest.mark.workflow(record_type="cat")
    def test_cat_service_process_vendor_file(
        self,
        fake_matcher,
        caplog,
        mock_marc,
        tmp_path,
        stub_update_service,
        stub_parsing_service,
        stub_uow,
    ):
        path = tmp_path / "temp"
        out = ProcessCatalogingRecords.execute(
            workflow_id=1,
            updater=stub_update_service,
            parser=stub_parsing_service,
            matcher=fake_matcher,
            storage=file_io.LocalFileStorage(base_path=path),
            uow=stub_uow,
        )
        assert out["id"] is not None
        assert "Integrity validation: True, missing_barcodes: []" in [
            i.msg for i in caplog.records
        ]

    @pytest.mark.workflow(record_type="cat")
    def test_cat_service_process_vendor_file_missing_barcodes(
        self,
        fake_matcher,
        missing_barcodes,
        caplog,
        mock_marc,
        tmp_path,
        stub_update_service,
        stub_parsing_service,
        stub_uow,
    ):
        path = tmp_path / "temp"
        out = ProcessCatalogingRecords.execute(
            workflow_id=1,
            updater=stub_update_service,
            parser=stub_parsing_service,
            matcher=fake_matcher,
            storage=file_io.LocalFileStorage(base_path=path),
            uow=stub_uow,
        )
        assert out["id"] is not None
        assert "Integrity validation: False, missing_barcodes: ['333330987654321']" in [
            i.msg for i in caplog.records
        ]
        assert "Barcodes integrity error: ['333330987654321']" in [
            i.msg for i in caplog.records
        ]

    @pytest.mark.workflow(record_type="sel")
    def test_sel_service_process_vendor_file(
        self,
        fake_matcher,
        mock_marc,
        tmp_path,
        stub_update_service,
        stub_parsing_service,
        stub_uow,
    ):
        path = tmp_path / "temp"
        out = ProcessSelectionRecords.execute(
            workflow_id=1,
            matcher=fake_matcher,
            updater=stub_update_service,
            parser=stub_parsing_service,
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
            storage=file_io.LocalFileStorage(base_path=path),
            uow=stub_uow,
        )
        assert out["id"] is not None

    @pytest.mark.workflow(record_type="acq")
    def test_acq_service_process_vendor_file(
        self,
        fake_matcher,
        mock_marc,
        tmp_path,
        stub_update_service,
        stub_parsing_service,
        stub_uow,
    ):
        path = tmp_path / "temp"
        out = ProcessAcquisitionsRecords.execute(
            workflow_id=1,
            updater=stub_update_service,
            parser=stub_parsing_service,
            matcher=fake_matcher,
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
            storage=file_io.LocalFileStorage(base_path=path),
            uow=stub_uow,
        )
        assert out["id"] is not None

    @pytest.mark.workflow(record_type="cat")
    def test_cat_service_process_vendor_file_dupes(
        self,
        fake_matcher,
        stub_uow,
        mock_marc_dupes,
        tmp_path,
        stub_update_service,
        stub_parsing_service,
    ):
        path = tmp_path / "temp"
        with pytest.raises(ValueError) as exc:
            ProcessCatalogingRecords.execute(
                workflow_id=1,
                updater=stub_update_service,
                parser=stub_parsing_service,
                matcher=fake_matcher,
                storage=file_io.LocalFileStorage(base_path=path),
                uow=stub_uow,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)

    @pytest.mark.workflow(record_type="acq")
    def test_acq_service_process_vendor_file_dupes(
        self,
        fake_matcher,
        mock_marc_dupes,
        tmp_path,
        stub_update_service,
        stub_parsing_service,
        stub_uow,
    ):
        path = tmp_path / "temp"
        with pytest.raises(ValueError) as exc:
            ProcessAcquisitionsRecords.execute(
                workflow_id=1,
                matcher=fake_matcher,
                template_data={"format": "a"},
                matchpoints={"primary_matchpoint": "isbn", "vendor": "UNKNOWN"},
                updater=stub_update_service,
                parser=stub_parsing_service,
                storage=file_io.LocalFileStorage(base_path=path),
                uow=stub_uow,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)

    @pytest.mark.workflow(record_type="sel")
    def test_sel_service_process_vendor_file_dupes(
        self,
        fake_matcher,
        mock_marc_dupes,
        tmp_path,
        stub_update_service,
        stub_parsing_service,
        stub_uow,
    ):
        path = tmp_path / "temp"
        with pytest.raises(ValueError) as exc:
            ProcessSelectionRecords.execute(
                workflow_id=1,
                matcher=fake_matcher,
                template_data={"format": "a"},
                matchpoints={"primary_matchpoint": "isbn", "vendor": "UNKNOWN"},
                updater=stub_update_service,
                parser=stub_parsing_service,
                storage=file_io.LocalFileStorage(base_path=path),
                uow=stub_uow,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)
