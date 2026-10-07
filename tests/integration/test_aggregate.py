import pytest

from overload_web.domain.pvf import aggregate, models, services
from overload_web.infrastructure import marc_handler


def create_stub_bib(record_type: str):
    return models.DomainBib(
        library="nypl",
        collection="BL",
        isbn="9781234567890",
        title="Foo",
        record_type=record_type,
        binary_data=b"",
        barcodes=["333331234567890"],
        orders=[],
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


@pytest.fixture
def stub_updater_service():
    return services.BibUpdater(
        handler=marc_handler.MarcUpdater(),
        order_mapping={},
        default_loc="foo",
        bib_id_tag="bar",
        library="baz",
        record_type="quz",
        collection="spam",
    )


@pytest.fixture
def stub_order_level_job():
    job = aggregate.OrderLevelJob(workflow_id="1", vendor="UNKNOWN")
    job.file_names = ["foo.mrc"]
    job.report_data = []
    job.file_records = {"foo.mrc": [create_stub_bib("acq")]}
    job.file_records["foo.mrc"][0].action = "insert"
    return job


@pytest.fixture
def stub_full_record_job():
    job = aggregate.FullRecordJob(workflow_id="1")
    bib = create_stub_bib("cat")
    job.file_names = ["foo.mrc"]
    job.records = [bib]
    job.records[0].action = "attach"
    job.report_data = []
    job.original_barcodes = bib.barcodes
    return job


@pytest.fixture
def fake_matcher(fake_fetcher):
    return services.BibMatcher(fetcher=fake_fetcher)


@pytest.fixture
def mock_parsing_service(monkeypatch):
    def mock_parse_marc_data(*args, **kwargs):
        return [create_stub_bib("acq")]

    def mock_write(*args, **kwargs):
        return b""

    monkeypatch.setattr(services.BibParser, "parse_marc_data", mock_parse_marc_data)
    monkeypatch.setattr(services.BibParser, "write", mock_write)
    return services.BibParser(
        handler=marc_handler.MarcParser(),
        library="foo",
        record_type="bar",
        collection="baz",
        vendor_mapping={},
        bib_mapping={},
        order_mapping={},
    )


class TestOrderLevelJob:
    def test_order_level_job(self):
        job = aggregate.OrderLevelJob(workflow_id="1", vendor="UNKNOWN")
        assert job.file_names == []
        assert job.file_records == {}
        assert job.missing_barcodes == []
        assert job.processed_files == []
        assert job.report_data == []
        assert hasattr(job.validator, "validate_unique")

    def test_order_level_job_parse_files(self, mock_parsing_service):
        job = aggregate.OrderLevelJob(workflow_id="1", vendor="UNKNOWN")
        job.parse_files(batches_data={"foo.mrc": b""}, parser=mock_parsing_service)
        assert job.file_names == ["foo.mrc"]
        assert job.file_records["foo.mrc"][0].isbn == "9781234567890"
        assert job.missing_barcodes == []
        assert job.processed_files == []
        assert job.report_data == []

    def test_order_level_job_match_records(self, fake_matcher, stub_order_level_job):
        stub_order_level_job.match_records(
            matcher=fake_matcher, matchpoints={"primary_matchpoint": "isbn"}
        )
        assert stub_order_level_job.missing_barcodes == []
        assert stub_order_level_job.processed_files == []
        assert len(stub_order_level_job.report_data) == 1
        assert stub_order_level_job.report_data[0]["resource_id"] == "9781234567890"

    def test_order_level_job_apply_updates_and_create_batch(
        self, mock_parsing_service, stub_order_level_job, stub_updater_service
    ):
        processed_batch = stub_order_level_job.apply_updates_and_create_batch(
            parser=mock_parsing_service,
            template_data={"format": "a"},
            updater=stub_updater_service,
        )
        assert stub_order_level_job.missing_barcodes == []
        assert len(stub_order_level_job.processed_files) == 1
        assert processed_batch.files == stub_order_level_job.processed_files
        assert processed_batch.processing_integrity is True
        assert processed_batch.total_files == len(stub_order_level_job.file_names)
        assert processed_batch.total_records == len(stub_order_level_job.report_data)


class TestFullRecordJob:
    def test_full_record_job(self):
        job = aggregate.FullRecordJob(workflow_id="1")
        assert job.file_names == []
        assert job.records == []
        assert job.missing_barcodes == []
        assert job.original_barcodes == []
        assert job.processed_files == []
        assert job.report_data == []
        assert isinstance(job.out_file_name, str)
        assert hasattr(job.validator, "validate_unique")

    def test_full_record_job_parse_files(self, mock_parsing_service):
        job = aggregate.FullRecordJob(workflow_id="1")
        job.parse_files(batches_data={"foo.mrc": b""}, parser=mock_parsing_service)
        assert job.file_names == ["foo.mrc"]
        assert job.records[0].isbn == "9781234567890"
        assert job.missing_barcodes == []
        assert job.original_barcodes == ["333331234567890"]
        assert job.processed_files == []
        assert job.report_data == []

    def test_full_record_job_match_records(self, fake_matcher, stub_full_record_job):
        stub_full_record_job.match_records(matcher=fake_matcher)
        assert stub_full_record_job.missing_barcodes == []
        assert stub_full_record_job.processed_files == []
        assert len(stub_full_record_job.report_data) == 1
        assert stub_full_record_job.report_data[0]["resource_id"] == "9781234567890"

    def test_full_record_job_apply_updates_and_create_batch(
        self, mock_parsing_service, stub_full_record_job, stub_updater_service
    ):
        processed_batch = stub_full_record_job.apply_updates_and_create_batch(
            parser=mock_parsing_service, updater=stub_updater_service
        )
        assert stub_full_record_job.missing_barcodes == []
        assert len(stub_full_record_job.processed_files) == 3
        assert processed_batch.files == stub_full_record_job.processed_files
        assert processed_batch.processing_integrity is True
        assert processed_batch.total_files == len(stub_full_record_job.file_names)
        assert processed_batch.total_records == len(stub_full_record_job.report_data)
