from __future__ import annotations

from collections import OrderedDict
from typing import Dict, List, Optional

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


def match(
    sierra_service: AbstractSierraSession,
    matchpoints: Dict[str, str],
) -> Optional[List[str]]:
    return sierra_service.order_matches(matchpoints=matchpoints)


def process_file(
    sierra_service: AbstractSierraSession,
    order_data: model.Order,
    template: model.OrderTemplate,
) -> model.OrderBib:
    matchpoint_dict = OrderedDict()
    for matchpoint in template.matchpoints:
        matchpoint_dict[matchpoint] = getattr(order_data, f"{matchpoint}")
    bib_id = sierra_service.match_bib(matchpoints=matchpoint_dict)
    order_bib = model.attach(order=order_data, bib_id=bib_id)
    return model.apply_template(bib=order_bib, template=template)
