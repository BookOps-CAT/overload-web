"""Application service for managing full vendor file processing workflow."""

import logging
from typing import Any

from overload_web.domain.pvf import commands, events, models, ports

logger = logging.getLogger(__name__)


class WorkflowManager:
    """Orchestrates workflows and tracks state."""

    def __init__(
        self, bus: ports.MessageBusPort, uow: ports.UnitOfWorkProtocol
    ) -> None:
        """Initialize the workflow manager with a unit of work and message bus.

        Args:
            bus: a `ports.MessageBusPort` object.
            uow: a `ports.UnitOfWorkProcotol` object.

        """
        self.bus = bus
        self.uow = uow

    def _update_workflow_state(
        self, id: str, state: dict[str, Any]
    ) -> models.WorkflowState | None:
        """Update the workflow state based on an event triggered by the workflow."""
        with self.uow:
            new_state = self.uow.workflow_states.update(id=id, data=state)
            self.uow.commit()
            if not new_state:
                logger.error(f"Cannot update state: Workflow {id} not found.")
            else:
                logger.info(f"Workflow {id} transitioned to {state['status']}")
        return new_state

    def handle_workflow_initialized(self, event: events.WorkflowInitialized) -> None:
        """Handle a `WorkflowInitialized` event creating a new workflow.

        Args:
            event: an `events.WorkflowInitialized` object containing a workflow ID

        Returns:
            None. New workflow is saved to db with the event's workflow_id
            and a `PENDING` state.

        """
        with self.uow:
            state = models.WorkflowStateBase(
                status=models.WorkflowStatus.PENDING, id=event.workflow_id
            )
            self.uow.workflow_states.save(state)
            self.uow.commit()
            logger.info(
                f"Workflow {event.workflow_id} created. Status is {state.status}."
            )

    def handle_workflow_started_order_level(
        self, event: events.OrderLevelWorkflowStarted
    ) -> None:
        """Handle a `OrderLevelWorkflowStarted` event starting an initialized workflow.

        Args:
            event:
                an `events.OrderLevelWorkflowStarted` object.
                The event contains the following attributes:
                    collection: str | None
                    library: str
                    matchpoints: dict[str, str]
                    record_type: str
                    template_data: dict[str, Any]
                    vendor: str
                    workflow_id: str

        Returns:
            None. Workflow state is updated to `PROCESSING` and
            `ParseOrderLevelFiles` command is sent to message bus.

        """
        state = self._update_workflow_state(
            id=event.workflow_id,
            state={
                "id": event.workflow_id,
                "status": models.WorkflowStatus.PROCESSING,
                "matchpoints": event.matchpoints,
                "template_data": event.template_data,
                "library": event.library,
                "collection": event.collection,
                "record_type": event.record_type,
            },
        )
        if not state:
            return
        self.bus.send(
            commands.ParseOrderLevelFiles(
                workflow_id=event.workflow_id,
                vendor=event.vendor,
                collection=state.collection,
                library=state.library,
                record_type=state.record_type,
            )
        )

    def handle_files_parsed_order_level(
        self, event: events.OrderLevelFilesParsed
    ) -> None:
        """Handle a `OrderLevelFilesParsed` event after file parsing.

        Args:
            event:
                an `events.OrderLevelFilesParsed` object containing
                the workflow ID.

        Returns:
            None. Workflow state is updated to `MATCHING` and
            `MatchOrderLevelRecords` command is sent to message bus.

        """
        state = self._update_workflow_state(
            id=event.workflow_id, state={"status": models.WorkflowStatus.MATCHING}
        )
        if not state:
            return
        self.bus.send(
            commands.MatchOrderLevelRecords(
                workflow_id=event.workflow_id,
                matchpoints=state.matchpoints,
                library=state.library,
            )
        )

    def handle_records_matched_order_level(
        self, event: events.OrderLevelRecordsMatched
    ) -> None:
        """Handle a `OrderLevelRecordsMatched` event after file parsing.

        Args:
            event:
                an `events.OrderLevelFilesParsed` object containing
                the workflow ID.

        Returns:
            None. Workflow state is updated to `UPDATING` and
            `UpdateAndOutputOrderLevelRecords` command is sent to message bus.

        """
        state = self._update_workflow_state(
            id=event.workflow_id, state={"status": models.WorkflowStatus.UPDATING}
        )
        if not state:
            return
        self.bus.send(
            commands.UpdateAndOutputOrderLevelRecords(
                workflow_id=event.workflow_id,
                template_data=state.template_data,
                library=state.library,
                collection=state.collection,
                record_type=state.record_type,
            )
        )

    def handle_workflow_started_full_level(
        self, event: events.FullLevelWorkflowStarted
    ) -> None:
        """Handle a `FullLevelWorkflowStarted` event starting an initialized workflow.

        Args:
            event:
                an `events.FullLevelWorkflowStarted` object.
                The event contains the following attributes:
                    collection: str | None
                    library: str
                    record_type: str
                    workflow_id: str

        Returns:
            None. Workflow state is updated to `PROCESSING` and
            `ParseFullLevelFiles` command is sent to message bus.

        """
        state = self._update_workflow_state(
            id=event.workflow_id,
            state={
                "id": event.workflow_id,
                "status": models.WorkflowStatus.PROCESSING,
                "library": event.library,
                "collection": event.collection,
                "record_type": event.record_type,
            },
        )
        if not state:
            return
        self.bus.send(
            commands.ParseFullLevelFiles(
                workflow_id=event.workflow_id,
                library=state.library,
                collection=state.collection,
                record_type=state.record_type,
            )
        )

    def handle_files_parsed_full_level(
        self, event: events.FullLevelFilesParsed
    ) -> None:
        """Handle a `FullLevelFilesParsed` event after records have been matched.

        Args:
            event:
                an `events.FullLevelFilesParsed` object containing
                the workflow ID.

        Returns:
            None. Workflow state is updated to `MATCHING` and
            `MatchFullLevelRecords` command is sent to message bus.

        """
        state = self._update_workflow_state(
            id=event.workflow_id, state={"status": models.WorkflowStatus.MATCHING}
        )
        if not state:
            return
        self.bus.send(
            commands.MatchFullLevelRecords(
                workflow_id=event.workflow_id, library=state.library
            )
        )

    def handle_records_matched_full_level(
        self, event: events.FullLevelRecordsMatched
    ) -> None:
        """Handle a `FullLevelRecordsMatched` event after records have been matched.

        Args:
            event:
                an `events.FullLevelRecordsMatched` object containing
                the workflow ID.

        Returns:
            None. Workflow state is updated to `UPDATING` and
            `UpdateAndOutputFullLevelRecords` command is sent to message bus.

        """
        state = self._update_workflow_state(
            id=event.workflow_id, state={"status": models.WorkflowStatus.UPDATING}
        )
        if not state:
            return
        self.bus.send(
            commands.UpdateAndOutputFullLevelRecords(
                workflow_id=event.workflow_id,
                library=state.library,
                record_type=state.record_type,
                collection=state.collection,
            )
        )

    def handle_workflow_completed(self, event: events.WorkflowCompleted) -> None:
        """Handle a `WorkflowCompleted` event after processing has completed.

        Args:
            event:
                an `events.WorkflowCompleted` object.
                The event contains the following attributes:
                    workflow_id: str
                    batch_id: str

        Returns:
            None. Workflow state is updated to `COMPLETED`.

        """
        self._update_workflow_state(
            id=event.workflow_id,
            state={
                "status": models.WorkflowStatus.COMPLETED,
                "batch_id": event.batch_id,
            },
        )
