from __future__ import annotations

from typing import List, Optional

from overload_web.adapters import object_factories, sierra_adapters
from overload_web.domain import model


def match_bib(
    bib: model.DomainBib,
    matchpoints: List[str],
    sierra_service: sierra_adapters.SierraService,
) -> model.DomainBib:
    bib_factory = object_factories.BibFactory()
    bibs = []
    for key in matchpoints:
        sierra_bibs = sierra_service.get_bibs_by_id(bib=bib, key=key)
        bibs.extend(
            [bib_factory.to_domain(i, library=bib.library) for i in sierra_bibs]
        )
    bib.match(bibs=bibs, matchpoints=matchpoints)
    return bib


def process_file(
    bib: model.DomainBib,
    sierra_service: sierra_adapters.SierraService,
    template: Optional[model.Template] = None,
    matchpoints: List[str] = [],
) -> model.DomainBib:
    if template:
        for order in bib.orders:
            order.apply_template(template=template)
        matchpoints = template.matchpoints
    return match_bib(bib=bib, matchpoints=matchpoints, sierra_service=sierra_service)
