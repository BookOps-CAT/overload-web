from __future__ import annotations

import datetime
import io

import pytest

from overload_web.adapters import marc_adapters, object_factories
from overload_web.api import schemas
from overload_web.domain import model


@pytest.fixture
def order_data():
    return {
        "audience": "a",
        "blanket_po": "baz",
        "copies": 13,
        "country": "xxu",
        "create_date": datetime.date(2025, 1, 1),
        "format": "b",
        "fund": "lease",
        "internal_note": "foo",
        "lang": "eng",
        "locations": ["agj0y"],
        "order_type": "l",
        "price": "{{dollar}}13.20",
        "selector": "j",
        "selector_note": "bar",
        "source": "d",
        "status": "o",
        "var_field_isbn": "bar",
        "vendor_code": "btlea",
        "vendor_notes": "baz",
        "vendor_title_no": "foo",
    }


@pytest.fixture
def order_bib_data(library, order_data):
    return {
        "library": library,
        "orders": [model.Order(**order_data)],
        "upc": None,
        "isbn": None,
        "bib_id": None,
        "oclc_number": [],
    }


@pytest.fixture
def template_data(order_data):
    template_data = {k: v for k, v in order_data.items() if k != "locations"}
    template_data["primary_matchpoint"] = "isbn"
    template_data["secondary_matchpoint"] = None
    template_data["tertiary_matchpoint"] = None
    return template_data


@pytest.fixture
def stub_order(obj_type, stub_960, stub_961, order_data):
    if obj_type == "domain":
        return model.Order(**order_data)
    elif obj_type == "pydantic":
        return schemas.OrderModel(**order_data)
    elif obj_type == "marc":
        return marc_adapters.OverloadOrder(stub_960, stub_961)
    else:
        return order_data


@pytest.fixture
def stub_order_bib(obj_type, library, stub_bib, order_bib_data):
    if obj_type == "domain":
        return model.OrderBib(**order_bib_data)
    elif obj_type == "pydantic":
        return schemas.OrderBibModel(**order_bib_data)
    elif obj_type == "marc":
        return marc_adapters.OverloadBib.from_bookops_bib(stub_bib)
    else:
        return order_bib_data


@pytest.fixture
def stub_template(obj_type, template_data):
    if obj_type == "domain":
        return model.Template(**template_data)
    elif obj_type == "pydantic":
        return schemas.TemplateModel(**template_data)
    else:
        return template_data


@pytest.fixture
def stub_saved_template(obj_type, template_data, id, name, agent):
    if obj_type == "domain":
        return model.Template(**template_data)
    elif obj_type == "pydantic":
        return schemas.TemplateModel(**template_data)
    template_data.update({"id": id, "name": name, "agent": agent})
    if obj_type == "domain_persistent":
        return model.PersistentTemplate(**template_data)
    elif obj_type == "pydantic_persistent":
        return schemas.PersistentTemplateModel(**template_data)
    else:
        return template_data


class TestGenericFactory:
    GENERIC_FACTORY: object_factories.GenericFactory = object_factories.GenericFactory()

    def test_to_domain(self):
        with pytest.raises(NotImplementedError) as exc:
            self.GENERIC_FACTORY.to_domain("foo")
        assert str(exc.value) == "Subclasses should implement this method."

    def test_to_pydantic(self):
        with pytest.raises(NotImplementedError) as exc:
            self.GENERIC_FACTORY.to_pydantic("foo")
        assert str(exc.value) == "Subclasses should implement this method."


@pytest.mark.parametrize(
    "obj_type, data_type",
    [
        ("domain", model.Order),
        ("pydantic", schemas.OrderModel),
        ("marc", marc_adapters.OverloadOrder),
    ],
)
class TestOrderFactory:
    ORDER_FACTORY: object_factories.GenericFactory = object_factories.OrderFactory()

    def test_common_transforms(self, stub_order, obj_type, data_type, order_data):
        order = self.ORDER_FACTORY._common_transforms(stub_order)
        assert isinstance(stub_order, data_type)
        assert isinstance(order, dict)
        assert order == order_data

    def test_to_domain(self, stub_order, obj_type, data_type, order_data):
        domain_order = model.Order(**order_data)
        order_to_domain = self.ORDER_FACTORY.to_domain(stub_order)
        assert isinstance(stub_order, data_type)
        assert isinstance(order_to_domain, model.Order)
        assert order_to_domain == domain_order

    def test_to_pydantic(self, stub_order, obj_type, data_type, order_data):
        pydantic_order = schemas.OrderModel(**order_data)
        order_to_pydantic = self.ORDER_FACTORY.to_pydantic(stub_order)
        assert isinstance(stub_order, data_type)
        assert isinstance(order_to_pydantic, schemas.OrderModel)
        assert order_to_pydantic == pydantic_order


@pytest.mark.parametrize(
    "obj_type, data_type",
    [
        ("domain", model.OrderBib),
        ("pydantic", schemas.OrderBibModel),
        ("marc", marc_adapters.OverloadBib),
    ],
)
@pytest.mark.parametrize("library", ["bpl", "nypl"])
class TestOrderBibFactory:
    ORDER_BIB_FACTORY: object_factories.GenericFactory = (
        object_factories.OrderBibFactory()
    )

    def test_common_transforms(self, library, stub_order_bib, data_type, order_data):
        domain_order = model.Order(**order_data)
        order_bib = self.ORDER_BIB_FACTORY._common_transforms(stub_order_bib)
        assert isinstance(stub_order_bib, data_type)
        assert isinstance(order_bib, dict)
        assert order_bib["library"] == library
        assert order_bib["orders"] == [domain_order]

    def test_to_domain(self, library, stub_order_bib, data_type, order_bib_data):
        domain_order_bib = model.OrderBib(**order_bib_data)
        order_bib_to_domain = self.ORDER_BIB_FACTORY.to_domain(stub_order_bib)
        assert isinstance(stub_order_bib, data_type)
        assert isinstance(order_bib_to_domain, model.OrderBib)
        assert order_bib_to_domain == domain_order_bib

    def test_to_pydantic(self, library, stub_order_bib, data_type, order_bib_data):
        pydantic_order = schemas.OrderBibModel(**order_bib_data)
        order_bib_to_pydantic = self.ORDER_BIB_FACTORY.to_pydantic(stub_order_bib)
        assert isinstance(stub_order_bib, data_type)
        assert isinstance(order_bib_to_pydantic, model.OrderBib)
        assert order_bib_to_pydantic == pydantic_order

    def test_binary_to_domain_list(
        self, library, stub_bib, data_type, obj_type, order_bib_data
    ):
        domain_order_bib = model.OrderBib(**order_bib_data)
        binary_bib = io.BytesIO(stub_bib.as_marc())
        domain_list = self.ORDER_BIB_FACTORY.binary_to_domain_list(binary_bib, library)
        assert isinstance(domain_list, list)
        assert isinstance(domain_list[0], model.OrderBib)
        assert domain_list == [domain_order_bib]

    def test_binary_to_pydantic_list(
        self, library, stub_bib, data_type, obj_type, order_bib_data
    ):
        pydantic_order_bib = schemas.OrderBibModel(**order_bib_data)
        binary_bib = io.BytesIO(stub_bib.as_marc())
        pydantic_list = self.ORDER_BIB_FACTORY.binary_to_pydantic_list(
            binary_bib, library
        )
        assert isinstance(pydantic_list, list)
        assert isinstance(pydantic_list[0], schemas.OrderBibModel)
        assert pydantic_list == [pydantic_order_bib]


@pytest.mark.parametrize(
    "obj_type, data_type",
    [("domain", model.Template), ("pydantic", schemas.TemplateModel)],
)
class TestTemplateFactory:
    TEMPLATE_FACTORY: object_factories.GenericFactory = (
        object_factories.TemplateFactory()
    )

    def test_to_domain(self, obj_type, data_type, stub_template, template_data):
        domain_template = model.Template(**template_data)
        template_to_domain = self.TEMPLATE_FACTORY.to_domain(stub_template)
        assert isinstance(stub_template, data_type)
        assert isinstance(template_to_domain, model.Template)
        assert template_to_domain == domain_template

    def test_to_pydantic(self, obj_type, data_type, stub_template, template_data):
        pydantic_template = schemas.TemplateModel(**template_data)
        template_to_pydantic = self.TEMPLATE_FACTORY.to_pydantic(stub_template)
        assert isinstance(stub_template, data_type)
        assert isinstance(template_to_pydantic, schemas.TemplateModel)
        assert template_to_pydantic == pydantic_template


@pytest.mark.parametrize(
    "obj_type, data_type",
    [
        ("domain", model.Template),
        ("pydantic", schemas.TemplateModel),
        ("domain_persistent", model.PersistentTemplate),
        ("pydantic_persistent", schemas.PersistentTemplateModel),
    ],
)
@pytest.mark.parametrize("id, name, agent", [(1, "Foo Template", "user1")])
class TestPersistentTemplateFactory:
    TEMPLATE_FACTORY: object_factories.GenericFactory = (
        object_factories.PersistentTemplateFactory()
    )

    def test_to_domain(
        self, id, name, agent, obj_type, data_type, stub_saved_template, template_data
    ):
        template_data.update({"id": id, "name": name, "agent": agent})
        domain_template = model.PersistentTemplate(**template_data)
        template_to_domain = self.TEMPLATE_FACTORY.to_domain(
            stub_saved_template, id, name, agent
        )
        assert isinstance(stub_saved_template, data_type)
        assert isinstance(template_to_domain, model.PersistentTemplate)
        assert template_to_domain == domain_template

    def test_to_pydantic(
        self, id, name, agent, obj_type, data_type, stub_saved_template, template_data
    ):
        template_data.update({"id": id, "name": name, "agent": agent})
        pydantic_template = schemas.PersistentTemplateModel(**template_data)
        template_to_pydantic = self.TEMPLATE_FACTORY.to_pydantic(
            stub_saved_template, id, name, agent
        )
        assert isinstance(stub_saved_template, data_type)
        assert isinstance(template_to_pydantic, schemas.PersistentTemplateModel)
        assert template_to_pydantic == pydantic_template


class TestPersistentTemplateFactoryErrors:
    TEMPLATE_FACTORY: object_factories.GenericFactory = (
        object_factories.PersistentTemplateFactory()
    )

    @pytest.mark.parametrize(
        "obj_type, data_type",
        [
            ("domain", model.Template),
            ("pydantic", schemas.TemplateModel),
            ("domain_persistent", model.PersistentTemplate),
        ],
    )
    @pytest.mark.parametrize("id, name, agent", [(None, None, None)])
    def test_to_domain_missing_args(
        self, id, name, agent, obj_type, data_type, stub_saved_template
    ):
        with pytest.raises(TypeError) as exc:
            self.TEMPLATE_FACTORY.to_domain(stub_saved_template, id, name, agent)
        assert str(exc.value) == ""

    @pytest.mark.parametrize("id, name, agent", [(None, None, None)])
    def test_to_domain_missing_args_model(self, id, name, agent, template_data):
        template_data.update({"id": id, "name": name, "agent": agent})
        with pytest.raises(ValueError) as exc:
            self.TEMPLATE_FACTORY.to_domain(
                schemas.PersistentTemplateModel(**template_data), id, name, agent
            )
        assert "4 validation errors for PersistentTemplateModel" in str(exc.value)

    @pytest.mark.parametrize(
        "obj_type, data_type",
        [
            ("domain", model.Template),
            ("pydantic", schemas.TemplateModel),
            ("domain_persistent", model.PersistentTemplate),
        ],
    )
    @pytest.mark.parametrize("id, name, agent", [(None, None, None)])
    def test_to_pydantic_missing_args(
        self, id, name, agent, obj_type, data_type, stub_saved_template
    ):
        with pytest.raises(TypeError) as exc:
            self.TEMPLATE_FACTORY.to_pydantic(stub_saved_template, id, name, agent)
        assert str(exc.value) == ""

    @pytest.mark.parametrize("id, name, agent", [(None, None, None)])
    def test_to_pydantic_missing_args_model(self, id, name, agent, template_data):
        template_data.update({"id": id, "name": name, "agent": agent})
        with pytest.raises(ValueError) as exc:
            self.TEMPLATE_FACTORY.to_pydantic(
                schemas.PersistentTemplateModel(**template_data), id, name, agent
            )
        assert "4 validation errors for PersistentTemplateModel" in str(exc.value)
