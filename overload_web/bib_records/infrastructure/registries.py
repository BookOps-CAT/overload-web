import json
import logging
from functools import lru_cache
from typing import Any

from overload_web.bib_records.domain import bibs
from overload_web.bib_records.domain_services import matcher, serializer
from overload_web.bib_records.infrastructure.marc import mapper, update_strategy
from overload_web.bib_records.infrastructure.sierra import new_reviewer

logger = logging.getLogger(__name__)


@lru_cache
def load_constants() -> dict[str, Any]:
    with open("overload_web/vendor_specs.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    return constants


all_rules = load_constants()

order_level_parser = mapper.BookopsMarcOrderBibMapper(rules=all_rules["mapper_rules"])
full_record_parser = mapper.BookopsMarcFullBibMapper(rules=all_rules["mapper_rules"])


parser_registry = {
    bibs.Context("BL", "nypl", "acq"): order_level_parser,
    bibs.Context("BL", "nypl", "sel"): order_level_parser,
    bibs.Context("RL", "nypl", "acq"): order_level_parser,
    bibs.Context("RL", "nypl", "sel"): order_level_parser,
    bibs.Context("NONE", "bpl", "acq"): order_level_parser,
    bibs.Context("NONE", "bpl", "sel"): order_level_parser,
    bibs.Context("BL", "nypl", "cat"): full_record_parser,
    bibs.Context("RL", "nypl", "cat"): full_record_parser,
    bibs.Context("NONE", "bpl", "cat"): full_record_parser,
}

full_matcher = matcher.FullBibMatcher()
order_matcher = matcher.OrderBibMatcher()

matcher_registry = {
    bibs.Context("BL", "nypl", "acq"): order_matcher,
    bibs.Context("BL", "nypl", "sel"): order_matcher,
    bibs.Context("RL", "nypl", "acq"): order_matcher,
    bibs.Context("RL", "nypl", "sel"): order_matcher,
    bibs.Context("NONE", "bpl", "acq"): order_matcher,
    bibs.Context("NONE", "bpl", "sel"): order_matcher,
    bibs.Context("BL", "nypl", "cat"): full_matcher,
    bibs.Context("RL", "nypl", "cat"): full_matcher,
    bibs.Context("NONE", "bpl", "cat"): full_matcher,
}

bpl_reviewer = new_reviewer.BPLReviewer()
sel_reviewer = new_reviewer.SelectionReviewer()
acq_reviewer = new_reviewer.AcquisitionsReviewer()
nypl_BL_reviewer = new_reviewer.NYPLBranchReviewer()
nypl_RL_reviewer = new_reviewer.NYPLResearchReviewer()

attacher_registry = {
    bibs.Context("BL", "nypl", "acq"): acq_reviewer,
    bibs.Context("BL", "nypl", "sel"): sel_reviewer,
    bibs.Context("RL", "nypl", "acq"): acq_reviewer,
    bibs.Context("RL", "nypl", "sel"): sel_reviewer,
    bibs.Context("NONE", "bpl", "acq"): acq_reviewer,
    bibs.Context("NONE", "bpl", "sel"): sel_reviewer,
    bibs.Context("BL", "nypl", "cat"): nypl_BL_reviewer,
    bibs.Context("RL", "nypl", "cat"): nypl_RL_reviewer,
    bibs.Context("NONE", "bpl", "cat"): bpl_reviewer,
}

acq_updater = update_strategy.AcquisitionsUpdateStrategy(
    rules=all_rules["updater_rules"]
)
cat_updater = update_strategy.CatalogingUpdateStrategy(rules=all_rules["updater_rules"])
sel_updater = update_strategy.SelectionUpdateStrategy(rules=all_rules["updater_rules"])

updater_registry = {
    bibs.Context("BL", "nypl", "acq"): acq_updater,
    bibs.Context("BL", "nypl", "sel"): sel_updater,
    bibs.Context("RL", "nypl", "acq"): acq_updater,
    bibs.Context("RL", "nypl", "sel"): sel_updater,
    bibs.Context("NONE", "bpl", "acq"): acq_updater,
    bibs.Context("NONE", "bpl", "sel"): sel_updater,
    bibs.Context("BL", "nypl", "cat"): cat_updater,
    bibs.Context("RL", "nypl", "cat"): cat_updater,
    bibs.Context("NONE", "bpl", "cat"): cat_updater,
}

bib_serializer = serializer.BibSerializer()
