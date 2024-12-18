from __future__ import annotations

from typing import List, Optional

from overload_web.domain import model
from overload_web.sierra_adapters import AbstractSierraSession


def apply_template(
    bib: model.OrderBib, template: model.OrderTemplate
) -> model.OrderBib:
    model.apply_template(bib, template)
    return bib


def attach(order_data: model.Order, matched_bib_id: str) -> model.OrderBib:
    bib = model.attach(order=order_data, bib_id=matched_bib_id)
    return bib


def match(
    order_data: model.Order,
    sierra_service: AbstractSierraSession,
    matchpoints: List[str],
) -> Optional[List[str]]:
    return sierra_service.match_order(order=order_data, matchpoints=matchpoints)
