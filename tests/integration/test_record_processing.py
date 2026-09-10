import pytest
from sqlmodel import Session, SQLModel, create_engine

from overload_web.application.pvf.process import (
    ProcessAcquisitionsRecords,
    ProcessCatalogingRecords,
    ProcessSelectionRecords,
)
from overload_web.infrastructure import batch_db, marc_handler

# @pytest.fixture(scope="class")
# def test_session():
#     batch1 = batch_db.PVFBatch(
#         files=[batch_db.ProcessedFileModel(file_name="foo.mrc", records=b"")],
#         stats=[
#             {
#                 "action": "insert",
#                 "call_number": "Foo",
#                 "call_number_match": False,
#                 "duplicate_records": [],
#                 "mixed": [],
#                 "other": [],
#                 "resource_id": "12345",
#                 "target_bib_id": "23456",
#                 "target_call_no": "Foo",
#                 "target_title": None,
#                 "updated_by_vendor": False,
#                 "vendor": "UNKNOWN",
#             }
#         ],
#         file_names=["foo.mrc"],
#         total_files=1,
#         total_records=1,
#         missing_barcodes=[],
#         processing_integrity=True,
#     )
#     batch2 = batch_db.PVFBatch(
#         files=[batch_db.ProcessedFileModel(file_name="bar.mrc", records=b"")],
#         stats=[
#             {
#                 "action": "insert",
#                 "call_number": "Foo",
#                 "call_number_match": True,
#                 "duplicate_records": [],
#                 "mixed": [],
#                 "other": [],
#                 "resource_id": "12345",
#                 "target_bib_id": "23456",
#                 "target_call_no": "Foo",
#                 "target_title": None,
#                 "updated_by_vendor": False,
#                 "vendor": "UNKNOWN",
#             }
#         ],
#         file_names=["foo.mrc"],
#         total_files=1,
#         total_records=1,
#         missing_barcodes=[],
#         processing_integrity=True,
#     )
#     test_engine = create_engine("sqlite:///:memory:")
#     SQLModel.metadata.create_all(test_engine)
#     with Session(test_engine) as session:
#         session.add(batch1)
#         session.commit()
#         session.add(batch2)
#         session.commit()
#         yield session
#     session.close()
#     test_engine.dispose()


# @pytest.fixture(scope="class")
# def test_session_no_records():
#     test_engine = create_engine("sqlite:///:memory:")
#     SQLModel.metadata.create_all(test_engine)
#     with Session(test_engine) as session:
#         yield session
#     session.close()
#     test_engine.dispose()


@pytest.fixture(scope="class")
def stub_repo():
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield batch_db.PVFBatchRepository(session=session)
    session.close()
    test_engine.dispose()


@pytest.fixture
def update_rules(library, record_type, collection, get_constants):
    constants = get_constants["constants"]
    return {
        "order_mapping": constants["order_mapping"],
        "default_loc": constants["default_locations"][library].get(collection),
        "bib_id_tag": constants["bib_id_tag"][library],
        "library": library,
        "record_type": record_type,
        "collection": collection,
    }


class TestProcessCommands:
    ENGINE = marc_handler.MarcUpdateHandler()

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_cat_service_process_vendor_file(
        self, library, fake_fetcher, stub_repo, parsing_handler, update_rules
    ):
        with open(f"tests/data/{library}-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        out = ProcessCatalogingRecords.execute(
            batches={"foo.mrc": marc_data},
            marc_handler=self.ENGINE,
            marc_update_rules=update_rules,
            fetcher=fake_fetcher,
            repo=stub_repo,
            marc_parser=parsing_handler,
        )
        assert out["id"] is not None

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
    )
    def test_sel_service_process_vendor_file(
        self, library, fake_fetcher, stub_repo, parsing_handler, update_rules
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
            repo=stub_repo,
            marc_parser=parsing_handler,
        )
        assert out["id"] is not None

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "acq"), ("nypl", "RL", "acq"), ("bpl", "NONE", "acq")],
    )
    def test_acq_service_process_vendor_file(
        self, library, fake_fetcher, stub_repo, parsing_handler, update_rules
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
            repo=stub_repo,
            marc_parser=parsing_handler,
        )
        assert out["id"] is not None

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "cat"), ("nypl", "RL", "cat"), ("bpl", "NONE", "cat")],
    )
    def test_cat_service_process_vendor_file_dupes(
        self, library, fake_fetcher, stub_repo, parsing_handler, update_rules
    ):
        with open(f"tests/data/{library}-dupes-sample.mrc", "rb") as fh:
            marc_data = fh.read()
        with pytest.raises(ValueError) as exc:
            ProcessCatalogingRecords.execute(
                batches={"foo.mrc": marc_data},
                marc_handler=self.ENGINE,
                fetcher=fake_fetcher,
                marc_update_rules=update_rules,
                repo=stub_repo,
                marc_parser=parsing_handler,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "acq"), ("nypl", "RL", "acq"), ("bpl", "NONE", "acq")],
    )
    def test_acq_service_process_vendor_file_dupes(
        self, library, fake_fetcher, stub_repo, parsing_handler, update_rules
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
                repo=stub_repo,
                marc_parser=parsing_handler,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)

    @pytest.mark.parametrize(
        "library, collection, record_type",
        [("nypl", "BL", "sel"), ("nypl", "RL", "sel"), ("bpl", "NONE", "sel")],
    )
    def test_sel_service_process_vendor_file_dupes(
        self, library, fake_fetcher, stub_repo, parsing_handler, update_rules
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
                repo=stub_repo,
                marc_parser=parsing_handler,
            )
        assert "Duplicate barcodes found in file: " in str(exc.value)
