import logging

import pytest
from sqlmodel import SQLModel, create_engine

from overload_web.domain.pvf import aggregate, files, models, order_templates
from overload_web.infrastructure import unit_of_work

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_engine():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


class TestSqlModelUnitOfWork:
    def test_uow(self, mock_engine):
        uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine)
        assert uow.session is None
        with uow:
            assert uow.session is not None

    def test_uow_exit_with_rollback(self, mock_engine):
        uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine)
        with pytest.raises(IndexError):
            with uow:
                empty = list()
                empty[1]

    def test_incoming_files(self, mock_engine):
        file = files.IncomingFile(
            id="1",
            workflow_id="12345",
            filename="foo.mrc",
            source="ftp",
            reference="bar/foo.mrc",
        )
        uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine)
        with uow:
            new_file = uow.incoming_files.save(file)
            new_file_data = new_file.model_dump()
            uow.commit()
            uow.incoming_files.delete(new_file.id)
            uow.commit()
            all_files = uow.incoming_files.list_by_id(id="12345")
        assert new_file_data == {
            "id": "1",
            "workflow_id": "12345",
            "filename": "foo.mrc",
            "source": "ftp",
            "reference": "bar/foo.mrc",
        }
        assert len(all_files) == 0

    def test_order_templates(self, mock_engine, caplog):
        template = order_templates.OrderTemplate(
            id=1, primary_matchpoint="isbn", name="foo", agent="bar"
        )
        update_data = order_templates.OrderTemplateBase(
            primary_matchpoint="oclc_number", name="foo", agent="bar"
        )
        uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine)
        with uow:
            new_template = uow.order_templates.save(template)
            new_template_data = new_template.model_dump()
            uow.commit()
            saved_template = uow.order_templates.get(new_template.id)
            saved_workflow_id = saved_template.id
            saved_template_primary = saved_template.primary_matchpoint
            uow.commit()
            updated_template = uow.order_templates.update(data=update_data, id="1")
            updated_template_id = updated_template.id
            updated_template_primary = updated_template.primary_matchpoint
            uow.commit()
            invalid_template = uow.order_templates.update(data=update_data, id="2")
            uow.commit()
            all_templates = uow.order_templates.list()
        assert new_template_data["primary_matchpoint"] == "isbn"
        assert new_template_data["format"] is None
        assert saved_workflow_id == 1
        assert saved_workflow_id == updated_template_id
        assert saved_template_primary != updated_template_primary
        assert len(all_templates) == 1
        assert invalid_template is None
        assert "Template '2' does not exist" in caplog.text

    def test_processed_batches(self, mock_engine):
        batch = aggregate.ProcessedFileBatch(
            files=[aggregate.ProcessedFile(file_name="foo.mrc", records=b"")],
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
            missing_barcodes=[],
        )
        uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine)
        with uow:
            new_batch = uow.processed_batches.save(batch)
            new_batch_data = new_batch.model_dump()
            uow.commit()
            saved_batch = uow.processed_batches.get(new_batch.id)
            saved_batch_data = saved_batch.model_dump()
            uow.commit()
            invalid_batch = uow.processed_batches.get(id="2")
            uow.commit()
        assert sorted(list(new_batch_data.keys())) == sorted(
            [
                "file_names",
                "total_records",
                "processing_integrity",
                "total_files",
                "id",
                "stats",
                "missing_barcodes",
            ]
        )
        assert new_batch_data == saved_batch_data
        assert invalid_batch is None

    def test_workflow_states(self, mock_engine, caplog):
        workflow = models.WorkflowState(
            status=models.WorkflowStatus.PENDING,
            id="1",
            library="foo",
            collection="bar",
            record_type="baz",
        )
        update_data = models.WorkflowStateBase(status=models.WorkflowStatus.PROCESSING)
        uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine)
        with uow:
            new_workflow = uow.workflow_states.save(workflow)
            new_workflow_status = new_workflow.status
            uow.commit()
            saved_workflow = uow.workflow_states.get(new_workflow.id)
            saved_workflow_id = saved_workflow.id
            saved_workflow_status = saved_workflow.status
            uow.commit()
            updated_workflow = uow.workflow_states.update(data=update_data, id="1")
            updated_workflow_id = updated_workflow.id
            updated_workflow_status = updated_workflow.status
            uow.commit()
            invalid_workflow = uow.workflow_states.update(data=update_data, id="2")
            uow.commit()
        assert new_workflow_status == "PENDING"
        assert saved_workflow_id == "1"
        assert saved_workflow_id == updated_workflow_id
        assert saved_workflow_status != updated_workflow_status
        assert invalid_workflow is None
        assert "Workflow '2' does not exist" in caplog.text
