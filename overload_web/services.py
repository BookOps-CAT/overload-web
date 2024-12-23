from __future__ import annotations


from typing import List

from overload_web.domain import model
from overload_web.sierra_adapters import SierraService


def apply_template(
    bib: model.OrderBib, template: model.OrderTemplate
) -> model.OrderBib:
    model.apply_template(bib, template)
    return bib


def attach(order_data: model.Order, bib_ids: List[str]) -> model.OrderBib:
    bib = model.OrderBib(order=order_data)
    bib.attach(bib_ids)
    return bib


def process_file(
    sierra_service: SierraService,
    order_data: model.Order,
    template: model.OrderTemplate,
) -> model.OrderBib:
    order_bib = model.OrderBib(
        order=order_data,
    )
    order_bib.attach(sierra_service.get_all_bib_ids(order_data, template.matchpoints))
    return model.apply_template(bib=order_bib, template=template)
