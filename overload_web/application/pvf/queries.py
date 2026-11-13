"""Read queries for process vendor file workflow."""

from typing import Any

from overload_web.domain.pvf import aggregate, files, models, order_templates, ports


def get_batch_data(
    batch_id: str, uow: ports.UnitOfWorkProtocol
) -> aggregate.ProcessedFileBatch:
    """Get all processed files and report data from a processed batch."""
    with uow:
        data = uow.processed_batches.get(batch_id)
        if not data:
            raise ValueError(f"Batch {batch_id} not found in database.")
        return data


def get_detailed_report_data(
    batch_id: str, uow: ports.UnitOfWorkProtocol
) -> list[dict[str, Any]]:
    """Create a detailed processing report for a batch of processed records."""
    with uow:
        data = uow.processed_batches.get(batch_id)
        if data:
            return data.stats
    return []


def get_order_template(
    template_id: str, uow: ports.UnitOfWorkProtocol
) -> order_templates.OrderTemplate | None:
    """Retrieve an order template by its ID."""
    with uow:
        data = uow.order_templates.get(id=template_id)
        return order_templates.OrderTemplate(**data.model_dump()) if data else None


def get_processed_file(
    file_id: str, uow: ports.UnitOfWorkProtocol
) -> files.VendorFile | None:
    """Get a processed file from the database."""
    with uow:
        file = uow.processed_files.get(file_id)
        if file:
            return files.VendorFile(filename=file.filename, content=file.records)
    return None


def get_workflow_state(
    workflow_id: str, uow: ports.UnitOfWorkProtocol
) -> models.WorkflowState | None:
    """Get current status of workflow."""
    with uow:
        data = uow.workflow_states.get(workflow_id)
        if data:
            return data
    return None


def get_processing_report(
    batch_id: str, uow: ports.UnitOfWorkProtocol
) -> dict[str, Any]:
    """Create a report summary for a batch of processed records."""
    with uow:
        data = uow.processed_batches.get(batch_id)
        if data:
            return {
                "total_records": data.total_records,
                "file_names": data.file_names,
                "total_files": data.total_files,
                "vendor_report": data.vendor_report,
                "duplicate_report": data.duplicate_report,
                "missing_barcodes": data.missing_barcodes,
                "processing_integrity": data.processing_integrity,
                "call_number_report": data.call_number_report,
            }
    return {}


def list_order_templates(
    uow: ports.UnitOfWorkProtocol, offset: int, limit: int
) -> list[order_templates.OrderTemplate]:
    """List all order templates."""
    with uow:
        template_list = uow.order_templates.list(offset=offset, limit=limit)
        return [order_templates.OrderTemplate(**i.model_dump()) for i in template_list]


def list_workflow_files(
    workflow_id: str, uow: ports.UnitOfWorkProtocol
) -> list[dict[str, Any]]:
    """List all files associated with a workflow ID."""
    with uow:
        files = uow.incoming_files.list_by_id(workflow_id)
        return [f.model_dump() for f in files]
