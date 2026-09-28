import logging

from sqlmodel import Field, Session, SQLModel

from overload_web.domain.pvf import workflow

logger = logging.getLogger(__name__)


class WorkflowJobModel(SQLModel, table=True):
    """SQLModel table definition for storing WorkflowJob state."""

    __tablename__ = "workflow_jobs"

    id: str = Field(primary_key=True)
    status: workflow.JobStatus = Field(default=workflow.JobStatus.PENDING)
    error_message: str | None
    record_type: str


class WorkflowJobRepository:
    """
    `SQLModel` repository for `WorkflowJob` objects.

    This class is a concrete implementation of the `SqlRepositoryProtocol` protocol.

    Args:
        session: a `sqlmodel.Session`.
    """

    def __init__(self, session: Session):
        self.session = session

    def delete(self, id: str) -> None:
        """Delete a workflow job by ID."""
        db_obj = self.session.get(WorkflowJobModel, id)
        if db_obj:
            self.session.delete(db_obj)

    def get(self, id: str | int) -> workflow.WorkflowJob | None:
        """Retrieve a workflow job by ID and map it to a domain object."""
        db_obj = self.session.get(WorkflowJobModel, id)
        if not db_obj:
            return None
        return workflow.WorkflowJob(
            id=db_obj.id,
            status=db_obj.status,
            error_message=db_obj.error_message,
            record_type=db_obj.record_type,
        )

    def save(self, job: workflow.WorkflowJob) -> None:
        """
        Adds a new `IncomingFileModel` to the database.

        Args:
            obj: the `IncomingFileModel` object to save.

        Returns:
            The `IncomingFileModel` data as a dictionary.
        """
        valid_obj = WorkflowJobModel.model_validate(job, from_attributes=True)
        self.session.add(valid_obj)

    def update(self, id: str, job: workflow.WorkflowJob) -> workflow.WorkflowJob | None:
        """Update an existing workflow job state."""
        db_obj = self.session.get(WorkflowJobModel, id)
        if not db_obj:
            return None

        db_obj.status = job.status
        db_obj.error_message = job.error_message
        if job.record_type:
            db_obj.record_type = job.record_type

        self.session.add(db_obj)
        return job
