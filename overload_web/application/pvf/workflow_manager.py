import logging
from typing import Any

from overload_web.domain.pvf import commands, events, models, ports

logger = logging.getLogger(__name__)


class WorkflowManager:
    """Orchestrates workflows and tracks state."""

    def __init__(self, bus: ports.MessageBusPort, uow: ports.UnitOfWorkProtocol):
        self.bus = bus
        self.uow = uow

    def handle_workflow_started_order_level(
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

    def handle_files_parsed_order_level(
        self, event: events.OrderLevelFilesParsed
    ) -> None:
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

    def handle_records_matched_order_level(
        self, event: events.OrderLevelRecordsMatched
    ) -> None:
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

    def handle_workflow_completed_order_level(
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

    def handle_workflow_started_full_level(self, workflow_id: str) -> None:
        """Triggered by the FastAPI endpoint."""
        new_status = models.WorkflowStatus.PROCESSING
        with self.uow:
            state = self.uow.workflow_states.get(workflow_id)
            if not state:
                logger.error(f"Cannot update state: Workflow {workflow_id} not found.")
                return
            state.status = new_status
            self.uow.workflow_states.update(id=workflow_id, data=state)
            self.uow.commit()
            logger.info(f"Workflow {workflow_id} transitioned to {new_status}")
        self.bus.send(commands.ParseFullLevelFiles(workflow_id=workflow_id))

    def handle_files_parsed_full_level(
        self, event: events.FullLevelFilesParsed
    ) -> None:
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
            self.uow.commit()
            logger.info(f"Workflow {event.workflow_id} transitioned to {new_status}")
        self.bus.send(commands.MatchFullLevelRecords(workflow_id=event.workflow_id))

    def handle_records_matched_full_level(
        self, event: events.FullLevelRecordsMatched
    ) -> None:
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
            self.uow.commit()
            logger.info(f"Workflow {event.workflow_id} transitioned to {new_status}")
        self.bus.send(
            commands.UpdateAndOutputFullLevelRecords(workflow_id=event.workflow_id)
        )

    def handle_workflow_completed_full_level(
        self, event: events.FullLevelWorkflowCompleted
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
