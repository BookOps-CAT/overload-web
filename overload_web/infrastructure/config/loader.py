import json
import logging
from typing import Any

from overload_web.infrastructure.marc import engine

logger = logging.getLogger(__name__)


def load_config() -> dict[str, Any]:
    """Retrieve processing constants from JSON file."""
    with open("overload_web/data/mapping_specs.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return constants


def marc_engine_config_from_constants(
    constants: dict[str, Any], library: str, collection: str | None, record_type: str
) -> engine.MarcEngineConfig:
    return engine.MarcEngineConfig(
        marc_order_mapping=constants["marc_order_mapping"],
        default_loc=constants["default_locations"][library].get(collection),
        bib_id_tag=constants["bib_id_tag"][library],
        library=library,
        record_type=record_type,
        parser_bib_mapping=constants["bib_domain_mapping"],
        parser_order_mapping=constants["order_domain_mapping"],
        parser_vendor_mapping=constants["vendor_info_options"][library],
    )
