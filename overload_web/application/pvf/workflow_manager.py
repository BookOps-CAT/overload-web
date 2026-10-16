import logging
from typing import Any

from overload_web.domain.pvf import commands, events, models, ports

logger = logging.getLogger(__name__)


class WorkflowManager:
    """Orchestrates workflows and tracks state."""

    def __init__(self, bus: ports.MessageBusPort, uow: ports.UnitOfWorkProtocol):
        self.bus = bus
        self.uow = uow

    def handle_workflow_event(
        self, id: str, state: models.WorkflowStateBase
    ) -> models.WorkflowState | None:
        """Handle an event triggered by the workflow."""
        with self.uow:
            new_state = self.uow.workflow_states.update(id=id, data=state)
            self.uow.commit()
            if not new_state:
                logger.error(f"Cannot update state: Workflow {id} not found.")
            else:
                logger.info(f"Workflow {id} transitioned to {state.status}")
        return new_state

    def handle_workflow_started_order_level(
        self,
        workflow_id: str,
        vendor: str,
        matchpoints: dict[str, Any],
        template_data: dict[str, Any],
    ) -> None:
        """Triggered by the FastAPI endpoint."""
        state = self.handle_workflow_event(
            id=workflow_id,
            state=models.WorkflowStateBase(
                status=models.WorkflowStatus.PROCESSING,
                matchpoints=matchpoints,
                template_data=template_data,
            ),
        )
        if not state:
            return
        self.bus.send(
            commands.ParseOrderLevelFiles(workflow_id=workflow_id, vendor=vendor)
        )

    def handle_files_parsed_order_level(
        self, event: events.OrderLevelFilesParsed
    ) -> None:
        state = self.handle_workflow_event(
            id=event.workflow_id,
            state=models.WorkflowStateBase(status=models.WorkflowStatus.MATCHING),
        )
        if not state:
            return
        self.bus.send(
            commands.MatchOrderLevelRecords(
                workflow_id=event.workflow_id, matchpoints=state.matchpoints
            )
        )

    def handle_records_matched_order_level(
        self, event: events.OrderLevelRecordsMatched
    ) -> None:
        state = self.handle_workflow_event(
            id=event.workflow_id,
            state=models.WorkflowStateBase(status=models.WorkflowStatus.UPDATING),
        )
        if not state:
            return
        self.bus.send(
            commands.UpdateAndOutputOrderLevelRecords(
                workflow_id=event.workflow_id, template_data=state.template_data
            )
        )

    def handle_workflow_completed_order_level(
        self, event: events.OrderLevelWorkflowCompleted
    ) -> None:
        self.handle_workflow_event(
            id=event.workflow_id,
            state=models.WorkflowStateBase(
                status=models.WorkflowStatus.COMPLETED, batch_id=event.batch_id
            ),
        )

    def handle_workflow_started_full_level(self, workflow_id: str) -> None:
        """Triggered by the FastAPI endpoint."""
        state = self.handle_workflow_event(
            id=workflow_id,
            state=models.WorkflowStateBase(status=models.WorkflowStatus.PROCESSING),
        )
        if not state:
            return
        self.bus.send(commands.ParseFullLevelFiles(workflow_id=workflow_id))

    def handle_files_parsed_full_level(
        self, event: events.FullLevelFilesParsed
    ) -> None:
        state = self.handle_workflow_event(
            id=event.workflow_id,
            state=models.WorkflowStateBase(status=models.WorkflowStatus.MATCHING),
        )
        if not state:
            return
        self.bus.send(commands.MatchFullLevelRecords(workflow_id=event.workflow_id))

    def handle_records_matched_full_level(
        self, event: events.FullLevelRecordsMatched
    ) -> None:
        state = self.handle_workflow_event(
            id=event.workflow_id,
            state=models.WorkflowStateBase(status=models.WorkflowStatus.UPDATING),
        )
        if not state:
            return
        self.bus.send(
            commands.UpdateAndOutputFullLevelRecords(workflow_id=event.workflow_id)
        )

    def handle_workflow_completed_full_level(
        self, event: events.FullLevelWorkflowCompleted
    ) -> None:
        self.handle_workflow_event(
            id=event.workflow_id,
            state=models.WorkflowStateBase(
                status=models.WorkflowStatus.COMPLETED, batch_id=event.batch_id
            ),
        )
