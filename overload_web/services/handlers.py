from __future__ import annotations

from overload_web.adapters import sierra_adapters
from overload_web.domain import model


def apply_template(bib: model.DomainBib, template: model.Template) -> model.DomainBib:
    bib.apply_template(template=template)
    return bib


def process_file(
    bib: model.DomainBib,
    sierra_service: sierra_adapters.SierraService,
    template: model.Template,
) -> model.DomainBib:
    bib.attach(
        sierra_service.get_all_bib_ids(order_bib=bib, match_keys=template.matchpoints)
    )
    bib.apply_template(template=template)
    return bib
