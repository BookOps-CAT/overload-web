import pytest
from sqlmodel import Session, SQLModel, create_engine

from overload_web.application.commands.process import (
    ProcessAcquisitionsRecords,
    ProcessCatalogingRecords,
    ProcessSelectionRecords,
)
from overload_web.application.commands.reporting import (
    CreatePVFOutputReport,
    GetDetailedReportData,
    WriteOutputReport,
)
from overload_web.infrastructure import batch_db, marc_engine, reporter


@pytest.fixture(scope="class")
def test_session():
    batch1 = batch_db.PVFBatch(
        files=[batch_db.ProcessedFileModel(file_name="foo.mrc", records=b"")],
        report=batch_db.PVFReportModel(
            id=1,
            action=["insert"],
            call_number=["Foo"],
            call_number_match=[False],
            duplicate_records=[[]],
            file_names=["foo.mrc"],
            mixed=[[]],
            other=[[]],
            resource_id=["12345"],
            target_bib_id=["23456"],
            target_call_no=["Foo"],
            target_title=[],
            total_files=1,
            total_records=1,
            updated_by_vendor=[False],
            vendor=["UNKNOWN"],
            missing_barcodes=[],
            processing_integrity=True,
        ),
    )
    batch2 = batch_db.PVFBatch(
        files=[batch_db.ProcessedFileModel(file_name="bar.mrc", records=b"")],
        report=batch_db.PVFReportModel(
            id=2,
            action=["insert"],
            call_number=["Foo"],
            call_number_match=[True],
            duplicate_records=[[]],
            file_names=["foo.mrc"],
            mixed=[[]],
            other=[[]],
            resource_id=["12345"],
            target_bib_id=["23456"],
            target_call_no=["Foo"],
            target_title=[],
            total_files=1,
            total_records=1,
            updated_by_vendor=[False],
            vendor=["UNKNOWN"],
            missing_barcodes=[],
            processing_integrity=True,
        ),
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


class TestProcessCommands:
    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_cat_service_process_vendor_file(
        self, library, fake_fetcher, engine_config, test_session
    ):
        repo = batch_db.PVFBatchRepository(session=test_session)
        engine = marc_engine.MarcEngine(rules=engine_config)
        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        out = ProcessCatalogingRecords.execute(
            batches={"foo.mrc": marc_data},
            marc_engine=engine,
            fetcher=fake_fetcher,
            repo=repo,
        )
        assert out["id"] is not None

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
    )
    def test_sel_service_process_vendor_file(
        self, library, fake_fetcher, engine_config, test_session
    ):
        engine = marc_engine.MarcEngine(rules=engine_config)
        repo = batch_db.PVFBatchRepository(session=test_session)
        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        out = ProcessSelectionRecords.execute(
            {"foo.mrc": marc_data},
            marc_engine=engine,
            fetcher=fake_fetcher,
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
            repo=repo,
        )
        assert out["id"] is not None

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "acq"), ("nypl", "RL", "acq"), ("bpl", "NONE", "acq")],
    )
    def test_acq_service_process_vendor_file(
        self, library, fake_fetcher, engine_config, test_session
    ):
        engine = marc_engine.MarcEngine(rules=engine_config)
        repo = batch_db.PVFBatchRepository(session=test_session)
        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        out = ProcessAcquisitionsRecords.execute(
            {"foo.mrc": marc_data},
            marc_engine=engine,
            fetcher=fake_fetcher,
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
            repo=repo,
        )
        assert out["id"] is not None

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_cat_service_process_vendor_file_dupes(
        self, library, fake_fetcher, engine_config, test_session
    ):
        engine = marc_engine.MarcEngine(rules=engine_config)
        repo = batch_db.PVFBatchRepository(session=test_session)
        with open(f"tests/data/{library}-dupes-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        with pytest.raises(ValueError) as exc:
            ProcessCatalogingRecords.execute(
                batches={"foo.mrc": marc_data},
                marc_engine=engine,
                fetcher=fake_fetcher,
                repo=repo,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "acq"), ("nypl", "RL", "acq"), ("bpl", "NONE", "acq")],
    )
    def test_acq_service_process_vendor_file_dupes(
        self, library, fake_fetcher, engine_config, test_session
    ):
        engine = marc_engine.MarcEngine(rules=engine_config)
        repo = batch_db.PVFBatchRepository(session=test_session)
        with open(f"tests/data/{library}-dupes-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        with pytest.raises(ValueError) as exc:
            ProcessAcquisitionsRecords.execute(
                {"foo.mrc": marc_data},
                marc_engine=engine,
                fetcher=fake_fetcher,
                template_data={"format": "a"},
                matchpoints={"primary_matchpoint": "isbn", "vendor": "UNKNOWN"},
                repo=repo,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
    )
    def test_sel_service_process_vendor_file_dupes(
        self, library, fake_fetcher, engine_config, test_session
    ):
        engine = marc_engine.MarcEngine(rules=engine_config)
        repo = batch_db.PVFBatchRepository(session=test_session)
        with open(f"tests/data/{library}-dupes-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        with pytest.raises(ValueError) as exc:
            ProcessSelectionRecords.execute(
                {"foo.mrc": marc_data},
                marc_engine=engine,
                fetcher=fake_fetcher,
                template_data={"format": "a"},
                matchpoints={"primary_matchpoint": "isbn", "vendor": "UNKNOWN"},
                repo=repo,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)


@pytest.fixture(scope="class")
def test_session_no_records():
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    session.close()
    test_engine.dispose()


class TestReportCommands:
    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_create_pvf_output_report(
        self, mock_sheet_config, caplog, test_session, record_type
    ):
        repo = batch_db.PVFBatchRepository(session=test_session)
        out = CreatePVFOutputReport.execute(
            batch_id="1",
            handler=reporter.PandasReportHandler(),
            record_type=record_type,
            repo=repo,
        )
        assert "total_records" in out.keys()
        assert "file_names" in out.keys()
        assert "total_files" in out.keys()

    def test_get_detailed_report_data(self, mock_sheet_config, caplog, test_session):
        repo = batch_db.PVFBatchRepository(session=test_session)
        out = GetDetailedReportData.execute(
            batch_id="1", handler=reporter.PandasReportHandler(), repo=repo
        )
        assert sorted([i for i in out.keys()]) == sorted(
            [
                "vendor",
                "resource_id",
                "action",
                "target_bib_id",
                "updated_by_vendor",
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
        self, mock_sheet_config, caplog, test_session, record_type
    ):
        repo = batch_db.PVFBatchRepository(session=test_session)
        WriteOutputReport.execute(
            batch_id="1",
            handler=reporter.PandasReportHandler(),
            record_type=record_type,
            repo=repo,
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
        self, mock_sheet_config, caplog, test_session, record_type
    ):
        repo = batch_db.PVFBatchRepository(session=test_session)
        WriteOutputReport.execute(
            batch_id=2,
            handler=reporter.PandasReportHandler(),
            record_type=record_type,
            repo=repo,
            writer=reporter.GoogleSheetsReporter(),
        )
        assert len(caplog.records) == 1
        assert (
            "Data written to Google Sheet: {'spreadsheetId': 'foo', 'tableRange': 'bar'}"
            in caplog.text
        )

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_write_output_report_no_reports(
        self, mock_sheet_config, caplog, test_session_no_records, record_type
    ):
        repo = batch_db.PVFBatchRepository(session=test_session_no_records)
        WriteOutputReport.execute(
            batch_id=2,
            handler=reporter.PandasReportHandler(),
            record_type=record_type,
            repo=repo,
            writer=reporter.GoogleSheetsReporter(),
        )
        assert len(caplog.records) == 0
