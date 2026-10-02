import pytest
from sqlmodel import SQLModel, create_engine

from overload_web.application.pvf.report_service import (
    CreatePVFOutputReport,
    GetDetailedReportData,
    WriteOutputReport,
)
from overload_web.infrastructure import reporter, tables, unit_of_work


class MockResource:
    def __init__(self):
        self.spreadsheetId = "foo"
        self.range = "bar"

    def append(self, *args, **kwargs):
        return self

    def execute(self, *args, **kwargs):
        return dict(spreadsheetId=self.spreadsheetId, tableRange=self.range)

    def spreadsheets(self, *args, **kwargs):
        return self

    def values(self, *args, **kwargs):
        return self


@pytest.fixture
def mock_sheet_service(monkeypatch) -> None:
    def mock_creds(*args, **kwargs):
        pass

    def build_sheet(*args, **kwargs):
        return MockResource()

    monkeypatch.setattr("googleapiclient.discovery.build", build_sheet)
    monkeypatch.setattr("googleapiclient.discovery.build_from_document", build_sheet)
    monkeypatch.setattr(reporter.GoogleSheetsReporter, "configure_sheet", mock_creds)


@pytest.fixture
def mock_stats():
    return {
        "action": "insert",
        "call_number": "Foo",
        "call_number_match": True,
        "duplicate_records": [],
        "mixed": [],
        "other": [],
        "resource_id": "12345",
        "target_bib_id": "23456",
        "target_call_no": "Foo",
        "target_title": None,
        "updated_by_vendor": False,
        "vendor": "UNKNOWN",
    }


@pytest.fixture
def stub_uow_no_data(monkeypatch):
    def mock_get(*args, **kwargs):
        pass

    monkeypatch.setattr("sqlmodel.Session.get", mock_get)
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    yield unit_of_work.SqlModelUnitOfWork(engine=test_engine)
    test_engine.dispose()


@pytest.fixture
def stub_uow_no_call_no_report(monkeypatch, mock_stats):
    def mock_get(*args, **kwargs):
        return tables.PVFBatch(
            files=[tables.ProcessedFileModel(file_name="foo.mrc", records=b"")],
            stats=[mock_stats],
            file_names=["foo.mrc"],
            total_files=1,
            total_records=1,
            missing_barcodes=[],
            processing_integrity=True,
        )

    monkeypatch.setattr("sqlmodel.Session.get", mock_get)
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    yield unit_of_work.SqlModelUnitOfWork(engine=test_engine)
    test_engine.dispose()


@pytest.fixture
def stub_uow_with_data(monkeypatch, mock_stats):
    def mock_get(*args, **kwargs):
        mock_stats["call_number_match"] = False
        return tables.PVFBatch(
            files=[tables.ProcessedFileModel(file_name="foo.mrc", records=b"")],
            stats=[mock_stats],
            file_names=["foo.mrc"],
            total_files=1,
            total_records=1,
            missing_barcodes=[],
            processing_integrity=True,
        )

    monkeypatch.setattr("sqlmodel.Session.get", mock_get)
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    yield unit_of_work.SqlModelUnitOfWork(engine=test_engine)
    test_engine.dispose()


class TestReportCommands:
    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_create_pvf_output_report(self, stub_uow_with_data, record_type):
        out = CreatePVFOutputReport.execute(
            batch_id="1", record_type=record_type, uow=stub_uow_with_data
        )
        assert out == {
            "total_records": 1,
            "file_names": ["foo.mrc"],
            "total_files": 1,
            "vendor_report": [
                {"vendor": "UNKNOWN", "attach": 0, "insert": 1, "update": 0, "total": 1}
            ],
            "dupes_report": [],
            "call_no_report": [
                {
                    "vendor": "UNKNOWN",
                    "resource_id": "12345",
                    "call_number": "Foo",
                    "target_bib_id": "23456",
                    "target_call_no": "Foo",
                    "call_number_match": False,
                    "duplicate_records": [],
                }
            ],
            "missing_barcodes": [],
            "processing_integrity": True,
        }

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_create_pvf_output_report_no_data(self, stub_uow_no_data, record_type):
        out = CreatePVFOutputReport.execute(
            batch_id="1", record_type=record_type, uow=stub_uow_no_data
        )
        assert out == {}

    def test_get_detailed_report_data(self, stub_uow_with_data):
        out = GetDetailedReportData.execute(batch_id="1", uow=stub_uow_with_data)
        assert sorted(out[0].keys()) == sorted(
            [
                "vendor",
                "resource_id",
                "action",
                "target_bib_id",
                "updated_by_vendor",
                "target_title",
                "call_number_match",
                "call_number",
                "target_call_no",
                "duplicate_records",
                "mixed",
                "other",
            ]
        )

    def test_get_detailed_report_data_no_data(self, stub_uow_no_data):
        out = GetDetailedReportData.execute(batch_id="1", uow=stub_uow_no_data)
        assert out == []

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_write_output_report_both_reports(
        self, mock_sheet_service, caplog, stub_uow_with_data, record_type
    ):
        WriteOutputReport.execute(
            batch_id="1",
            record_type=record_type,
            uow=stub_uow_with_data,
            writer=reporter.GoogleSheetsReporter(),
        )
        assert len(caplog.records) == 2
        assert (
            caplog.records[0].message
            == "Data written to Google Sheet: {'spreadsheetId': 'foo', 'tableRange': 'bar'}"
        )
        assert (
            caplog.records[1].message
            == "Data written to Google Sheet: {'spreadsheetId': 'foo', 'tableRange': 'bar'}"
        )

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_write_output_report_no_call_no_report(
        self, mock_sheet_service, caplog, stub_uow_no_call_no_report, record_type
    ):
        WriteOutputReport.execute(
            batch_id=2,
            record_type=record_type,
            uow=stub_uow_no_call_no_report,
            writer=reporter.GoogleSheetsReporter(),
        )
        assert len(caplog.records) == 1
        assert (
            "Data written to Google Sheet: {'spreadsheetId': 'foo', 'tableRange': 'bar'}"
            in caplog.text
        )

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_write_output_report_no_reports(
        self, mock_sheet_service, caplog, stub_uow_no_data, record_type
    ):
        WriteOutputReport.execute(
            batch_id=2,
            record_type=record_type,
            uow=stub_uow_no_data,
            writer=reporter.GoogleSheetsReporter(),
        )
        assert len(caplog.records) == 0
