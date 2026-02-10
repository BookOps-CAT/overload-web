import pandas as pd
import pytest

from overload_web.domain.models import reports
from overload_web.domain.services import match_analysis


class TestReport:
    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_report(self, full_bib, sierra_response, library, collection, record_type):
        rep = match_analysis.NYPLCatBranchMatchAnalyzer()
        result = rep.analyze(record=full_bib, candidates=[sierra_response])
        report = reports.FileReport(analyses=[result], file_name="foo.mrc")
        report_dict = report.to_dict()
        assert sorted(list(report_dict.keys())) == sorted(
            [
                "resource_id",
                "vendor",
                "updated_by_vendor",
                "call_number_match",
                "target_call_no",
                "call_number",
                "duplicate_records",
                "target_bib_id",
                "target_title",
                "mixed",
                "other",
                "action",
                "corrected",
                "file_name",
            ]
        )
        assert len(report_dict["action"]) == 1
        assert len(report_dict["call_number"]) == 1
        assert len(report_dict["call_number_match"]) == 1
        assert len(report_dict["duplicate_records"]) == 1
        assert len(report_dict["mixed"]) == 1
        assert len(report_dict["other"]) == 1
        assert len(report_dict["resource_id"]) == 1
        assert len(report_dict["target_bib_id"]) == 1
        assert len(report_dict["target_call_no"]) == 1
        assert len(report_dict["target_title"]) == 1
        assert len(report_dict["updated_by_vendor"]) == 1
        assert len(report_dict["vendor"]) == 1
        assert len(report_dict["corrected"]) == 1
        df = pd.DataFrame(data=report_dict)
        assert list(df.columns) == [
            "resource_id",
            "vendor",
            "updated_by_vendor",
            "call_number_match",
            "target_call_no",
            "call_number",
            "duplicate_records",
            "target_bib_id",
            "target_title",
            "mixed",
            "other",
            "action",
            "corrected",
            "file_name",
        ]
        assert df.shape == (1, 14)

    # @pytest.mark.parametrize(
    #     "library, collection, record_type",
    #     [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    # )
    # def test_pandas_report(
    #     self, full_bib, sierra_response, library, collection, record_type
    # ):
    #     rep = match_analysis.NYPLCatBranchMatchAnalyzer()
    #     result = rep.analyze(record=full_bib, candidates=[sierra_response])
    #     report = reports.FileReport(analyses=[result], file_name="foo.mrc")
    #     df = reporter.PandasReportHandler.vendor_breakdown(report=report)
    #     assert df == ""


# class MockCreds:
#     def __init__(self):
#         self.token = "foo"
#         self.refresh_token = "bar"

#     @property
#     def valid(self, *args, **kwargs):
#         return True

#     @property
#     def expired(self, *args, **kwargs):
#         return False

#     def refresh(self, *args, **kwargs):
#         self.expired = False
#         self.valid = True

#     def to_json(self, *args, **kwargs):
#         pass

#     def run_local_server(self, *args, **kwargs):
#         return self


# class MockResource:
#     def __init__(self):
#         self.spreadsheetId = "foo"
#         self.range = "bar"

#     def append(self, *args, **kwargs):
#         return self

#     def execute(self, *args, **kwargs):
#         return dict(spreadsheetId=self.spreadsheetId, tableRange=self.range)

#     def spreadsheets(self, *args, **kwargs):
#         return self

#     def values(self, *args, **kwargs):
#         return self


# @pytest.fixture
# def mock_open_file(mocker) -> None:
#     m = mocker.mock_open(read_data="")
#     mocker.patch("overload_web.bib_records.infrastructure.open", m)
#     mocker.patch("os.path.exists", lambda *args, **kwargs: True)


# @pytest.fixture
# def mock_sheet_config(monkeypatch, mock_open_file):
#     def build_sheet(*args, **kwargs):
#         return MockResource()

#     monkeypatch.setattr("googleapiclient.discovery.build", build_sheet)
#     monkeypatch.setattr("googleapiclient.discovery.build_from_document", build_sheet)
#     monkeypatch.setattr(
#         "google.oauth2.credentials.Credentials.from_authorized_user_info",
#         lambda *args, **kwargs: MockCreds(),
#     )


# # @pytest.fixture
# # def stub_reporter(mock_sheet_config):
# #     return reporter.GoogleSheetsReporter()


# # class TestReporter:
# #     def test_configure_sheet(self, mock_sheet_config):
# #         report = reporter.GoogleSheetsReporter()
# #         creds = report.configure_sheet()
# #         assert creds.token == "foo"
# #         assert creds.valid is True
# #         assert creds.expired is False
# #         assert creds.refresh_token is not None
