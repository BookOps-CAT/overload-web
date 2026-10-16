# import logging
# from dataclasses import dataclass
# from typing import Any

# import pytest
# from sqlmodel import SQLModel, create_engine

# from overload_web.domain.pvf import aggregate, files, models, order_templates
# from overload_web.domain.shared import Command, Event
# from overload_web.infrastructure import message_bus, unit_of_work
# from overload_web.presentation import schemas

# logger = logging.getLogger(__name__)


# @dataclass
# class StubCommand(Command):
#     id: str


# @dataclass
# class StubEvent(Event):
#     id: str


# @pytest.fixture
# def mock_engine():
#     engine = create_engine("sqlite:///:memory:")
#     SQLModel.metadata.create_all(engine)
#     yield engine
#     engine.dispose()


# class TestMessageBus:
#     def stub_callable(self, obj: Any) -> None:
#         logger.info(f"Caller for {obj}")

#     def test_message_bus(self):
#         bus = message_bus.MessageBus()
#         assert bus.command_handlers == {}
#         assert bus.event_handlers == {}

#     def test_register_command(self):
#         bus = message_bus.MessageBus()
#         bus.register_command(StubCommand, self.stub_callable)
#         assert len(bus.command_handlers.keys()) == 1
#         assert len(bus.event_handlers.keys()) == 0

#     def test_register_command_overwrite(self, caplog):
#         bus = message_bus.MessageBus()
#         bus.register_command(StubCommand, str)
#         bus.register_command(StubCommand, self.stub_callable)
#         assert len(bus.command_handlers.keys()) == 1
#         assert len(caplog.records) == 1
#         assert caplog.records[0].msg == "Overwriting handler for StubCommand"

#     def test_register_event(self):
#         bus = message_bus.MessageBus()
#         bus.register_event(StubEvent, self.stub_callable)
#         assert len(bus.command_handlers.keys()) == 0
#         assert len(bus.event_handlers.keys()) == 1

#     def test_register_event_overwrite(self):
#         bus = message_bus.MessageBus()
#         bus.register_event(StubEvent, self.stub_callable)
#         bus.register_event(StubEvent, self.stub_callable)
#         assert len(bus.command_handlers.keys()) == 0
#         assert len(bus.event_handlers.keys()) == 1

#     def test_send(self, caplog):
#         bus = message_bus.MessageBus()
#         bus.register_command(StubCommand, self.stub_callable)
#         bus.send(StubCommand(id="foo"))
#         assert len(caplog.records) == 2
#         assert caplog.records[0].msg == "Handling command: StubCommand"
#         assert caplog.records[1].msg == "Caller for StubCommand(id='foo')"

#     def test_send_missing_handler(self):
#         bus = message_bus.MessageBus()
#         with pytest.raises(ValueError) as exc:
#             bus.send(StubCommand(id="foo"))
#         assert str(exc.value) == "No handler registered for command StubCommand."

#     def test_publish(self, caplog):
#         bus = message_bus.MessageBus()
#         bus.register_event(StubEvent, self.stub_callable)
#         bus.publish(StubEvent(id="bar"))
#         assert len(caplog.records) == 2
#         assert caplog.records[0].msg == "Publishing event: StubEvent"
#         assert caplog.records[1].msg == "Caller for StubEvent(id='bar')"

#     def test_publish_missing_handler(self, caplog):
#         bus = message_bus.MessageBus()
#         bus.register_event(StubEvent, list)
#         bus.publish(StubEvent(id="bar"))
#         assert len(caplog.records) == 2
#         assert caplog.records[0].msg == "Publishing event: StubEvent"
#         assert (
#             caplog.records[1].msg
#             == "Error handling event StubEvent: 'StubEvent' object is not iterable"
#         )


# class TestSqlModelUnitOfWork:
#     def test_uow(self, mock_engine):
#         uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine)
#         assert uow.session is None
#         with uow:
#             assert uow.session is not None

#     def test_uow_exit_with_rollback(self, mock_engine):
#         uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine)
#         with pytest.raises(IndexError):
#             with uow:
#                 empty = list()
#                 empty[1]

#     def test_incoming_files(self, mock_engine):
#         file = files.IncomingFile(
#             id="1",
#             workflow_id="12345",
#             filename="foo.mrc",
#             source="ftp",
#             reference="bar/foo.mrc",
#         )
#         uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine)
#         with uow:
#             new_file = uow.incoming_files.save(file)
#         with uow:
#             uow.incoming_files.delete(new_file.id)
#         with uow:
#             all_files = uow.incoming_files.list_by_id(id="12345")
#         new_file_data = new_file.model_dump()
#         assert new_file_data == {
#             "id": "1",
#             "workflow_id": "12345",
#             "filename": "foo.mrc",
#             "source": "ftp",
#             "reference": "bar/foo.mrc",
#         }
#         assert len(all_files) == 0

#     def test_order_templates(self, mock_engine, caplog):
#         template = order_templates.OrderTemplate(
#             id=1, primary_matchpoint="isbn", name="foo", agent="bar"
#         )
#         update_data = schemas.TemplatePatchModel(
#             primary_matchpoint="oclc_number", name="foo", agent="bar"
#         )
#         uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine)
#         with uow:
#             new_template = uow.order_templates.save(template)
#         with uow:
#             saved_template = uow.order_templates.get(new_template.id)
#         with uow:
#             updated_template = uow.order_templates.update(data=update_data, id="1")
#         with uow:
#             invalid_template = uow.order_templates.update(data=update_data, id="2")
#         with uow:
#             all_templates = uow.order_templates.list()
#         new_template_data = new_template.model_dump()
#         assert new_template_data["primary_matchpoint"] == "isbn"
#         assert new_template_data["format"] is None
#         assert saved_template.id == 1
#         assert saved_template.id == updated_template.id
#         assert saved_template.primary_matchpoint != updated_template.primary_matchpoint
#         assert len(all_templates) == 1
#         assert invalid_template is None
#         assert "Template '2' does not exist" in caplog.text

#     def test_processed_batches(self, mock_engine):
#         batch = aggregate.ProcessedFileBatch(
#             files=[aggregate.ProcessedFile(file_name="foo.mrc", records=b"")],
#             stats=[
#                 {
#                     "action": "insert",
#                     "call_number": "Foo",
#                     "call_number_match": True,
#                     "duplicate_records": [],
#                     "mixed": [],
#                     "other": [],
#                     "resource_id": "12345",
#                     "target_bib_id": "23456",
#                     "target_call_no": "Foo",
#                     "target_title": None,
#                     "updated_by_vendor": False,
#                     "vendor": "UNKNOWN",
#                 }
#             ],
#             file_names=["foo.mrc"],
#             missing_barcodes=[],
#         )
#         uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine)
#         with uow:
#             new_batch = uow.processed_batches.save(batch)
#         with uow:
#             saved_batch = uow.processed_batches.get(new_batch.id)
#         with uow:
#             invalid_batch = uow.processed_batches.get(id="2")
#         new_batch_data = new_batch.model_dump()
#         saved_batch_data = saved_batch.model_dump()
#         assert sorted(list(new_batch_data.keys())) == sorted(
#             [
#                 "file_names",
#                 "total_records",
#                 "processing_integrity",
#                 "total_files",
#                 "id",
#                 "stats",
#                 "missing_barcodes",
#             ]
#         )
#         assert new_batch_data == saved_batch_data
#         assert invalid_batch is None

#     def test_workflow_states(self, mock_engine, caplog):
#         workflow = models.WorkflowState(status=models.WorkflowStatus.PENDING, id="1")
#         update_data = models.WorkflowStateBase(status=models.WorkflowStatus.PROCESSING)
#         uow = unit_of_work.SqlModelUnitOfWork(engine=mock_engine)
#         with uow:
#             new_workflow = uow.workflow_states.save(workflow)
#         with uow:
#             saved_workflow = uow.workflow_states.get(new_workflow.id)
#         with uow:
#             updated_workflow = uow.workflow_states.update(data=update_data, id="1")
#         with uow:
#             invalid_workflow = uow.workflow_states.update(data=update_data, id="2")
#         new_workflow_data = new_workflow.model_dump()
#         assert new_workflow_data["status"] == "PENDING"
#         assert saved_workflow.id == "1"
#         assert saved_workflow.id == updated_workflow.id
#         assert saved_workflow.status != updated_workflow.status
#         assert invalid_workflow is None
#         assert "Workflow '2' does not exist" in caplog.text
