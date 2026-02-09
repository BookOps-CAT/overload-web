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
