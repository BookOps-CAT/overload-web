from dataclasses import dataclass
from enum import StrEnum


class JobStatus(StrEnum):
    DRAFT = "draft"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowJob:
    id: str
    status: JobStatus
    record_type: str
    error_message: str | None = None
