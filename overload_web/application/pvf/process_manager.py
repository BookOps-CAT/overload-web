import logging
from typing import Any

from overload_web.application.pvf.process import ProcessFullRecords
from overload_web.domain.pvf import commands, events, models, ports, services

logger = logging.getLogger(__name__)


class OrderLevelWorkflowManager:
    """Orchestrates workflows and tracks state."""

    def __init__(self, bus: ports.MessageBusPort, uow: ports.UnitOfWorkProtocol):
        self.bus = bus
        self.uow = uow

    def handle_workflow_started(
        self,
        workflow_id: str,
        vendor: str,
        matchpoints: dict[str, Any],
        template_data: dict[str, Any],
    ) -> None:
        """Triggered by the FastAPI endpoint."""
        new_status = models.WorkflowStatus.PROCESSING
        with self.uow:
            state = self.uow.workflow_states.get(workflow_id)
            if not state:
                logger.error(f"Cannot update state: Workflow {workflow_id} not found.")
                return
            state.status = new_status
            state.matchpoints = matchpoints
            state.template_data = template_data
            self.uow.workflow_states.update(id=workflow_id, data=state)
            self.uow.commit()
            logger.info(f"Workflow {workflow_id} transitioned to {new_status}")
        self.bus.send(
            commands.ParseOrderLevelFiles(workflow_id=workflow_id, vendor=vendor)
        )

    def handle_files_parsed(self, event: events.OrderLevelFilesParsed) -> None:
        new_status = models.WorkflowStatus.MATCHING
        with self.uow:
            state = self.uow.workflow_states.get(event.workflow_id)
            if not state:
                logger.error(
                    f"Cannot update state: Workflow {event.workflow_id} not found."
                )
                return

            state.status = new_status
            self.uow.workflow_states.update(id=event.workflow_id, data=state)
            matchpoints = state.matchpoints
            self.uow.commit()
            logger.info(f"Workflow {event.workflow_id} transitioned to {new_status}")
        self.bus.send(
            commands.MatchOrderLevelRecords(
                workflow_id=event.workflow_id, matchpoints=matchpoints
            )
        )

    def handle_records_matched(self, event: events.OrderLevelRecordsMatched) -> None:
        new_status = models.WorkflowStatus.UPDATING
        with self.uow:
            state = self.uow.workflow_states.get(event.workflow_id)
            if not state:
                logger.error(
                    f"Cannot update state: Workflow {event.workflow_id} not found."
                )
                return

            state.status = new_status
            self.uow.workflow_states.update(id=event.workflow_id, data=state)
            template_data = state.template_data
            self.uow.commit()
            logger.info(f"Workflow {event.workflow_id} transitioned to {new_status}")
        self.bus.send(
            commands.UpdateAndOutputOrderLevelRecords(
                workflow_id=event.workflow_id, template_data=template_data
            )
        )

    def handle_workflow_completed(
        self, event: events.OrderLevelWorkflowCompleted
    ) -> None:
        new_status = models.WorkflowStatus.COMPLETED
        with self.uow:
            state = self.uow.workflow_states.get(event.workflow_id)
            if not state:
                logger.error(
                    f"Cannot update state: Workflow {event.workflow_id} not found."
                )
                return

            state.status = new_status
            state.batch_id = event.batch_id
            self.uow.workflow_states.update(id=event.workflow_id, data=state)
            self.uow.commit()
            logger.info(f"Workflow {event.workflow_id} transitioned to {new_status}")


class FullLevelWorkflowManager:
    """Orchestrates workflows and tracks state."""

    @staticmethod
    def start_full_level_workflow(
        matcher: services.BibMatcher,
        parser: services.BibParser,
        storage: ports.FileStorage,
        updater: services.BibUpdater,
        uow: ports.UnitOfWorkProtocol,
        workflow_id: str,
    ) -> None:
        # 1. Mark as Processing
        with uow:
            state = uow.workflow_states.get(workflow_id)
            if state:
                state.status = models.WorkflowStatus.PROCESSING
                uow.workflow_states.update(data=state, id=workflow_id)
                uow.commit()

        try:
            # 2. Execute existing monolithic application service
            batch_id = ProcessFullRecords.execute(
                matcher=matcher,
                parser=parser,
                storage=storage,
                updater=updater,
                uow=uow,
                workflow_id=workflow_id,
            )

            # 3. Mark as Completed and store the result ID
            with uow:
                state = uow.workflow_states.get(workflow_id)
                if state:
                    state.status = models.WorkflowStatus.COMPLETED
                    state.batch_id = batch_id
                    uow.workflow_states.update(data=state, id=workflow_id)
                    uow.commit()

        except Exception as e:
            with uow:
                state = uow.workflow_states.get(workflow_id)
                if state:
                    state.status = models.WorkflowStatus.FAILED
                    state.error_message = str(e)
                    uow.workflow_states.update(data=state, id=workflow_id)
                    uow.commit()
