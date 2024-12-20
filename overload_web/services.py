from __future__ import annotations


from typing import Optional

from overload_web.domain import model
from overload_web.sierra_adapters import AbstractSierraSession


def apply_template(
    bib: model.OrderBib, template: model.OrderTemplate
) -> model.OrderBib:
    model.apply_template(bib, template)
    return bib


def attach(order_data: model.Order, matched_bib_id: Optional[str]) -> model.OrderBib:
    bib = model.attach(order=order_data, bib_id=matched_bib_id)
    return bib


def process_file(
    sierra_service: AbstractSierraSession,
    order_data: model.Order,
    template: model.OrderTemplate,
) -> model.OrderBib:
    bib_id = None
    for matchpoint in template.matchpoints:
        bib_id = sierra_service.get_bib_id(
            matchpoint, getattr(order_data, f"{matchpoint}")
        )
        if not bib_id:
            continue
    order_bib = model.attach(order=order_data, bib_id=bib_id)
    return model.apply_template(bib=order_bib, template=template)
