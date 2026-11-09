"""Read queries for process vendor file workflow."""

from typing import Any

from overload_web.domain.pvf import order_templates, ports


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
