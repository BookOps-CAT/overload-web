import pytest

from overload_web.api import schemas
from overload_web.domain import model


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_OrderBibModel(stub_order, library):
    stub_orderbib = model.OrderBib(library=library, orders=[stub_order])
    order_bib = schemas.OrderBibModel(**stub_orderbib.__dict__)
    assert order_bib.model_dump() == {
        "bib_id": None,
        "isbn": None,
        "upc": None,
        "oclc_number": None,
        "orders": [stub_order.__dict__],
        "library": library,
    }


def test_TemplateModel(stub_template):
    template = schemas.TemplateModel(**stub_template.__dict__)
    assert template.model_dump() == stub_template.__dict__
