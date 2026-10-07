import random

import pytest

from overload_web.domain.pvf import aggregate, models


def create_stub_bib(library, collection, record_type):
    number = random.randint(0, 100)
    barcode = f"33333{str(number).zfill(10)}"
    return models.DomainBib(
        library=library,
        collection=collection,
        isbn="9781234567890",
        title="Foo",
        record_type=record_type,
        binary_data=b"",
        barcodes=[barcode],
        orders=[],
        vendor_info=models.VendorInfo(
            name="UNKNOWN", bib_fields=[], matchpoints={"primary_matchpoint": "isbn"}
        ),
        parsed_fields=[],
    )


@pytest.fixture
def stub_parsed_aggregate(request):
    marker = request.node.get_closest_marker("workflow")
    record_type = marker.kwargs["record_type"]
    record = create_stub_bib("bpl", None, record_type)
    if record_type == "cat":
        job = aggregate.FullRecordJob(workflow_id="1")
        job.records = [record]
        job.original_barcodes = record.barcodes
    else:
        job = aggregate.OrderLevelJob(workflow_id="1", vendor="UNKNOWN")
        job.file_records = {"foo.mrc": [record]}
    return job


@pytest.fixture
def stub_matched_aggregate(request):
    marker = request.node.get_closest_marker("workflow")
    record_type = marker.kwargs["record_type"]
    record = create_stub_bib("nypl", "RL", record_type)
    record.action = "attach"
    if record_type == "cat":
        job = aggregate.FullRecordJob(workflow_id="1")
        job.records = [record]
        job.original_barcodes = record.barcodes
    else:
        job = aggregate.OrderLevelJob(workflow_id="1", vendor="UNKNOWN")
        job.file_records = {"foo.mrc": [record]}
    job.report_data = []
    return job


class TestOrderLevelJob:
    @pytest.mark.workflow(record_type="acq")
    def test_parse_files(self, fake_parser):
        job = aggregate.OrderLevelJob(workflow_id="1", vendor="UNKNOWN")
        job.parse_files(
            parser=fake_parser, batches_data={"foo.mrc": b"", "bar.mrc": b""}
        )
        assert isinstance(job.file_records, dict)
        assert list(job.file_records.keys()) == ["foo.mrc", "bar.mrc"]
        assert len(job.file_records["foo.mrc"]) == 1
        assert job.file_names == ["foo.mrc", "bar.mrc"]

    @pytest.mark.workflow(record_type="acq")
    def test_match_records(self, stub_parsed_aggregate, fake_matcher):
        stub_parsed_aggregate.match_records(
            matcher=fake_matcher, matchpoints={"primary_matchpoint": "isbn"}
        )
        assert len(stub_parsed_aggregate.file_records["foo.mrc"]) == 1
        assert stub_parsed_aggregate.file_records["foo.mrc"][0].bib_id is None

    @pytest.mark.workflow(record_type="acq")
    def test_apply_updates_and_create_batch(
        self, stub_matched_aggregate, fake_parser, fake_updater
    ):
        processed_batch = stub_matched_aggregate.apply_updates_and_create_batch(
            parser=fake_parser, template_data={"format": "a"}, updater=fake_updater
        )
        assert stub_matched_aggregate.missing_barcodes == []
        assert len(stub_matched_aggregate.processed_files) == 1
        assert processed_batch.files == stub_matched_aggregate.processed_files
        assert processed_batch.processing_integrity is True
        assert processed_batch.total_files == len(stub_matched_aggregate.file_names)
        assert processed_batch.total_records == len(stub_matched_aggregate.report_data)


class TestFullRecordJob:
    @pytest.mark.workflow(record_type="cat")
    def test_parse_files(self, fake_parser):
        job = aggregate.FullRecordJob(workflow_id="1")
        job.parse_files(
            parser=fake_parser, batches_data={"foo.mrc": b"", "bar.mrc": b""}
        )
        assert isinstance(job.records, list)
        assert len(job.records) == 2
        assert job.file_names == ["foo.mrc", "bar.mrc"]
        assert len(job.original_barcodes) == 2

    @pytest.mark.workflow(record_type="cat")
    def test_match_records(self, stub_parsed_aggregate, fake_matcher):
        stub_parsed_aggregate.match_records(matcher=fake_matcher)
        assert len(stub_parsed_aggregate.records) == 1
        assert stub_parsed_aggregate.records[0].bib_id == "12345"

    @pytest.mark.workflow(record_type="cat")
    def test_apply_updates_and_create_batch(
        self, stub_matched_aggregate, fake_parser, fake_updater
    ):
        processed_batch = stub_matched_aggregate.apply_updates_and_create_batch(
            parser=fake_parser, updater=fake_updater
        )
        assert stub_matched_aggregate.missing_barcodes == []
        assert len(stub_matched_aggregate.processed_files) == 3
        assert processed_batch.files == stub_matched_aggregate.processed_files
        assert processed_batch.processing_integrity is True
        assert processed_batch.total_files == len(stub_matched_aggregate.file_names)
        assert processed_batch.total_records == len(stub_matched_aggregate.report_data)
