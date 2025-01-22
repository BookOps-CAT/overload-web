from __future__ import annotations
from typing import List
from overload_web.domain import model
from overload_web.adapters import sierra_adapters


def apply_template(
    bib: model.OrderBib, template: model.OrderTemplate
) -> model.OrderBib:
    model.apply_template(bib=bib, template=template)
    return bib


def attach(
    bib_ids: List[str], library: str, order_data: List[model.Order]
) -> model.OrderBib:
    bib = model.OrderBib(library=library, orders=order_data)
    bib.attach(bib_ids)
    return bib


def process_file(
    order_bib: model.OrderBib,
    sierra_service: sierra_adapters.SierraService,
    template: model.OrderTemplate,
) -> model.OrderBib:
    order_bib.attach(
        sierra_service.get_all_bib_ids(
            order_bib=order_bib, match_keys=template.matchpoints
        )
    )
    return model.apply_template(bib=order_bib, template=template)
