from __future__ import annotations

from overload_web.adapters import sierra_adapters
from overload_web.domain import model


def apply_template(bib: model.OrderBib, template: model.Template) -> model.OrderBib:
    model.apply_template(bib=bib, template=template)
    return bib


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
    return model.apply_template(bib=order_bib, template=template)
