import pytest

from overload_web.application.commands.process import (
    CombineMarcFiles,
    ProcessFullRecords,
    ProcessOrderRecords,
)
from overload_web.application.services import report_services
from overload_web.domain.errors import OverloadError
from overload_web.infrastructure import marc_engine, reporter


class TestProcessBatch:
    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_full_service_process_vendor_file(
        self, library, fake_fetcher, engine_config
    ):
        engine = marc_engine.MarcEngine(rules=engine_config)
        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        combined = CombineMarcFiles.execute(data=[marc_data], marc_engine=engine)
        out = ProcessFullRecords.execute(
            combined, marc_engine=engine, fetcher=fake_fetcher, file_names=["foo.mrc"]
        )
        assert isinstance(out.files, list)
        assert hasattr(out, "missing_barcodes")

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_order_service_process_vendor_file(
        self, library, fake_fetcher, engine_config
    ):
        engine = marc_engine.MarcEngine(rules=engine_config)

        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        out = ProcessOrderRecords.execute(
            {"foo.mrc": marc_data},
            marc_engine=engine,
            fetcher=fake_fetcher,
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
        )
        assert isinstance(out.files, list)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_full_service_process_vendor_file_dupes(
        self, library, fake_fetcher, engine_config
    ):
        engine = marc_engine.MarcEngine(rules=engine_config)

        with open(f"tests/data/{library}-dupes-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        with pytest.raises(OverloadError) as exc:
            ProcessFullRecords.execute(
                marc_data,
                marc_engine=engine,
                fetcher=fake_fetcher,
                file_names=["foo.mrc"],
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_order_service_process_vendor_file_dupes(
        self, library, fake_fetcher, engine_config
    ):
        engine = marc_engine.MarcEngine(rules=engine_config)

        with open(f"tests/data/{library}-dupes-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        with pytest.raises(OverloadError) as exc:
            ProcessOrderRecords.execute(
                {"foo.mrc": marc_data},
                marc_engine=engine,
                fetcher=fake_fetcher,
                template_data={"format": "a"},
                matchpoints={"primary_matchpoint": "isbn", "vendor": "UNKNOWN"},
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)


class TestWriteReport:
    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_full_service_process_vendor_file(
        self,
        library,
        fake_fetcher,
        engine_config,
        mock_sheet_config,
        caplog,
        collection,
        record_type,
    ):
        engine = marc_engine.MarcEngine(rules=engine_config)
        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        combined = CombineMarcFiles.execute(data=[marc_data], marc_engine=engine)
        out = ProcessFullRecords.execute(
            combined, marc_engine=engine, fetcher=fake_fetcher, file_names=["foo.mrc"]
        )
        assert isinstance(out.files, list)
        writer = reporter.GoogleSheetsReporter()
        report_services.ReportWriter.write_report_to_google_sheet(
            data=out.stats,
            handler=reporter.PandasReportHandler(),
            writer=writer,
            record_type=record_type,
        )
        assert (
            "Data written to Google Sheet: {'spreadsheetId': 'foo', 'tableRange': 'bar'}"
            in caplog.text
        )

    @pytest.mark.parametrize(
        "library, collection", [("nypl", "BL"), ("nypl", "RL"), ("bpl", "NONE")]
    )
    @pytest.mark.parametrize("record_type", ["acq", "sel"])
    def test_order_service_process_vendor_file(
        self,
        library,
        fake_fetcher,
        engine_config,
        mock_sheet_config,
        caplog,
        collection,
        record_type,
    ):
        engine = marc_engine.MarcEngine(rules=engine_config)
        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        out = ProcessOrderRecords.execute(
            {"foo.mrc": marc_data},
            marc_engine=engine,
            fetcher=fake_fetcher,
            template_data={"format": "a", "vendor": "UNKNOWN"},
            matchpoints={"primary_matchpoint": "isbn"},
        )
        writer = reporter.GoogleSheetsReporter()
        report_services.ReportWriter.write_report_to_google_sheet(
            data=out.stats,
            handler=reporter.PandasReportHandler(),
            writer=writer,
            record_type=record_type,
        )
        assert (
            "Data written to Google Sheet: {'spreadsheetId': 'foo', 'tableRange': 'bar'}"
            in caplog.text
        )

    @pytest.mark.parametrize("record_type", ["acq", "cat", "sel"])
    def test_create_output_report(self, record_type, stub_report):
        out = report_services.PVFReporter.create_output_report(
            data=stub_report.__dict__,
            handler=reporter.PandasReportHandler(),
            record_type=record_type,
        )
        assert "vendor_report" in out.keys()
        assert "dupes_report" in out.keys()
        assert "call_no_report" in out.keys()

    def test_create_detailed_report(self, stub_report):
        out = report_services.PVFReporter.create_detailed_report(
            data=stub_report.__dict__, handler=reporter.PandasReportHandler()
        )
        assert "vendor" in out.keys()
        assert "target_bib_id" in out.keys()
        assert "resource_id" in out.keys()
