from dataclasses import dataclass

from overload_web.domain.shared import Event


@dataclass
class OrderLevelFilesParsed(Event):
    """Event marking completion of order-level record parsing."""

    workflow_id: str


@dataclass
class OrderLevelRecordsMatched(Event):
    """Event marking completion of order-level record matching."""

    workflow_id: str


@dataclass
class OrderLevelWorkflowCompleted(Event):
    """Event marking completion of processing workflow for order-level records."""

    workflow_id: str
    batch_id: str


@dataclass
class FullLevelFilesParsed(Event):
    """Event marking completion of full MARC record parsing."""

    workflow_id: str


@dataclass
class FullLevelRecordsMatched(Event):
    """Event marking completion of full MARC record matching."""

    workflow_id: str


@dataclass
class FullLevelWorkflowCompleted(Event):
    """Event marking completion of processing workflow for full MARC records."""

    workflow_id: str
    batch_id: str
