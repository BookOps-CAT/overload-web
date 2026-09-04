import pytest
from sqlmodel import Session, SQLModel, create_engine

from overload_web.application.pvf.process import (
    ProcessAcquisitionsRecords,
    ProcessCatalogingRecords,
    ProcessSelectionRecords,
)
from overload_web.application.pvf.reporting import (
    CreatePVFOutputReport,
    GetDetailedReportData,
    WriteOutputReport,
)
from overload_web.infrastructure import batch_db, marc_handler, reporter


@pytest.fixture(scope="class")
def test_session():
    batch1 = batch_db.PVFBatch(
        files=[batch_db.ProcessedFileModel(file_name="foo.mrc", records=b"")],
        stats=[
            {
                "action": "insert",
                "call_number": "Foo",
                "call_number_match": False,
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
        ],
        file_names=["foo.mrc"],
        total_files=1,
        total_records=1,
        missing_barcodes=[],
        processing_integrity=True,
    )
    batch2 = batch_db.PVFBatch(
        files=[batch_db.ProcessedFileModel(file_name="bar.mrc", records=b"")],
        stats=[
            {
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
        ],
        file_names=["foo.mrc"],
        total_files=1,
        total_records=1,
        missing_barcodes=[],
        processing_integrity=True,
    )
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        session.add(batch1)
        session.commit()
        session.add(batch2)
        session.commit()
        yield session
    session.close()
    test_engine.dispose()


@pytest.fixture(scope="class")
def test_session_no_records():
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    session.close()
    test_engine.dispose()


@pytest.fixture(scope="class")
def test_batch_repository(test_session):
    return batch_db.PVFBatchRepository(session=test_session)


class TestProcessCommands:
    ENGINE = marc_handler.MarcUpdateHandler()

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_cat_service_process_vendor_file(
        self,
        library,
        fake_fetcher,
        test_batch_repository,
        parsing_handler,
        update_rules,
    ):
        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        out = ProcessCatalogingRecords.execute(
            batches={"foo.mrc": marc_data},
            marc_handler=self.ENGINE,
            marc_update_rules=update_rules,
            fetcher=fake_fetcher,
            repo=test_batch_repository,
            marc_parser=parsing_handler,
        )
        assert out["id"] is not None

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
    )
    def test_sel_service_process_vendor_file(
        self,
        library,
        fake_fetcher,
        test_batch_repository,
        parsing_handler,
        update_rules,
    ):
        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        out = ProcessSelectionRecords.execute(
            {"foo.mrc": marc_data},
            marc_handler=self.ENGINE,
            fetcher=fake_fetcher,
            marc_update_rules=update_rules,
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
            repo=test_batch_repository,
            marc_parser=parsing_handler,
        )
        assert out["id"] is not None

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "acq"), ("nypl", "RL", "acq"), ("bpl", "NONE", "acq")],
    )
    def test_acq_service_process_vendor_file(
        self,
        library,
        fake_fetcher,
        test_batch_repository,
        parsing_handler,
        update_rules,
    ):
        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        out = ProcessAcquisitionsRecords.execute(
            {"foo.mrc": marc_data},
            marc_handler=self.ENGINE,
            fetcher=fake_fetcher,
            marc_update_rules=update_rules,
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
            repo=test_batch_repository,
            marc_parser=parsing_handler,
        )
        assert out["id"] is not None

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_cat_service_process_vendor_file_dupes(
        self,
        library,
        fake_fetcher,
        test_batch_repository,
        parsing_handler,
        update_rules,
    ):
        with open(f"tests/data/{library}-dupes-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        with pytest.raises(ValueError) as exc:
            ProcessCatalogingRecords.execute(
                batches={"foo.mrc": marc_data},
                marc_handler=self.ENGINE,
                fetcher=fake_fetcher,
                marc_update_rules=update_rules,
                repo=test_batch_repository,
                marc_parser=parsing_handler,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "acq"), ("nypl", "RL", "acq"), ("bpl", "NONE", "acq")],
    )
    def test_acq_service_process_vendor_file_dupes(
        self,
        library,
        fake_fetcher,
        test_batch_repository,
        parsing_handler,
        update_rules,
    ):
        with open(f"tests/data/{library}-dupes-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        with pytest.raises(ValueError) as exc:
            ProcessAcquisitionsRecords.execute(
                {"foo.mrc": marc_data},
                marc_handler=self.ENGINE,
                fetcher=fake_fetcher,
                marc_update_rules=update_rules,
                template_data={"format": "a"},
                matchpoints={"primary_matchpoint": "isbn", "vendor": "UNKNOWN"},
                repo=test_batch_repository,
                marc_parser=parsing_handler,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
    )
    def test_sel_service_process_vendor_file_dupes(
        self,
        library,
        fake_fetcher,
        test_batch_repository,
        parsing_handler,
        update_rules,
    ):
        with open(f"tests/data/{library}-dupes-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        with pytest.raises(ValueError) as exc:
            ProcessSelectionRecords.execute(
                {"foo.mrc": marc_data},
                marc_handler=self.ENGINE,
                fetcher=fake_fetcher,
                marc_update_rules=update_rules,
                template_data={"format": "a"},
                matchpoints={"primary_matchpoint": "isbn", "vendor": "UNKNOWN"},
                repo=test_batch_repository,
                marc_parser=parsing_handler,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)


class TestReportCommands:
    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_create_pvf_output_report(self, test_batch_repository, record_type):
        out = CreatePVFOutputReport.execute(
            batch_id="1", record_type=record_type, repo=test_batch_repository
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

    def test_get_detailed_report_data(self, test_batch_repository):
        out = GetDetailedReportData.execute(batch_id="1", repo=test_batch_repository)
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

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_write_output_report_both_reports(
        self, mock_sheet_service, caplog, test_batch_repository, record_type
    ):
        WriteOutputReport.execute(
            batch_id="1",
            record_type=record_type,
            repo=test_batch_repository,
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
        self, mock_sheet_service, caplog, test_batch_repository, record_type
    ):
        WriteOutputReport.execute(
            batch_id=2,
            record_type=record_type,
            repo=test_batch_repository,
            writer=reporter.GoogleSheetsReporter(),
        )
        assert len(caplog.records) == 1
        assert (
            "Data written to Google Sheet: {'spreadsheetId': 'foo', 'tableRange': 'bar'}"
            in caplog.text
        )

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_write_output_report_no_reports(
        self, mock_sheet_service, caplog, test_session_no_records, record_type
    ):
        repo = batch_db.PVFBatchRepository(session=test_session_no_records)
        WriteOutputReport.execute(
            batch_id=2,
            record_type=record_type,
            repo=repo,
            writer=reporter.GoogleSheetsReporter(),
        )
        assert len(caplog.records) == 0
