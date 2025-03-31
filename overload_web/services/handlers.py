from __future__ import annotations

from overload_web.adapters import sierra_adapters
from overload_web.domain import model


def apply_template(
    order_bib: model.OrderBib, template: model.Template
) -> model.OrderBib:
    order_bib.apply_template(template=template)
    return order_bib


def process_file(
    order_bib: model.OrderBib,
    sierra_service: sierra_adapters.SierraService,
    template: model.Template,
) -> model.OrderBib:
    order_bib.attach(
        sierra_service.get_all_bib_ids(
            order_bib=order_bib, match_keys=template.matchpoints
        )
    )
    order_bib.apply_template(template=template)
    return order_bib
