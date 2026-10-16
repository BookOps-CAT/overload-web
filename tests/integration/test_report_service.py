import pytest

from overload_web.application.pvf.report_service import (
    CreatePVFOutputReport,
    GetDetailedReportData,
    WriteOutputReport,
)
from overload_web.domain.pvf import reporting
from overload_web.infrastructure import reporter


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
def missing_call_no_report(monkeypatch):
    def null_return(*args, **kwargs):
        return None

    monkeypatch.setattr(
        reporting.ProcessingStatistics, "create_call_number_report", null_return
    )


class TestReportCommands:
    def test_create_pvf_output_report(self, fake_uow):
        out = CreatePVFOutputReport.execute(
            batch_id="1", record_type="acq", uow=fake_uow
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

    def test_create_pvf_output_report_no_data(self, fake_uow_no_data):
        out = CreatePVFOutputReport.execute(
            batch_id="1", record_type="cat", uow=fake_uow_no_data
        )
        assert out == {}

    def test_get_detailed_report_data(self, fake_uow):
        out = GetDetailedReportData.execute(batch_id="1", uow=fake_uow)
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

    def test_get_detailed_report_data_no_data(self, fake_uow_no_data):
        out = GetDetailedReportData.execute(batch_id="1", uow=fake_uow_no_data)
        assert out == []

    def test_write_output_report(self, mock_sheet_service, caplog, fake_uow):
        WriteOutputReport.execute(
            batch_id="1",
            record_type="cat",
            uow=fake_uow,
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

    def test_write_output_report_no_call_no_report(
        self, mock_sheet_service, caplog, fake_uow, missing_call_no_report
    ):
        WriteOutputReport.execute(
            batch_id=2,
            record_type="sel",
            uow=fake_uow,
            writer=reporter.GoogleSheetsReporter(),
        )
        assert len(caplog.records) == 1
        assert (
            "Data written to Google Sheet: {'spreadsheetId': 'foo', 'tableRange': 'bar'}"
            in caplog.text
        )

    def test_write_output_report_no_data(
        self, mock_sheet_service, caplog, fake_uow_no_data
    ):
        WriteOutputReport.execute(
            batch_id=2,
            record_type="acq",
            uow=fake_uow_no_data,
            writer=reporter.GoogleSheetsReporter(),
        )
        assert len(caplog.records) == 0
