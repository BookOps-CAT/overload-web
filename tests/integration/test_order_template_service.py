import inspect

import pytest
from sqlmodel import SQLModel, create_engine

from overload_web.application.pvf.template_handling import (
    GetOrderTemplate,
    ListOrderTemplates,
    SaveNewOrderTemplate,
    UpdateOrderTemplate,
)
from overload_web.domain.pvf import order_templates
from overload_web.infrastructure import template_db, unit_of_work
from overload_web.presentation import schemas


@pytest.fixture
def make_template():
    def _make_template(data):
        template = template_db.TemplateModel(**data)
        return template

    return _make_template


@pytest.fixture
def mock_engine():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def stub_uow(mock_engine):
    return unit_of_work.SqlModelUnitOfWork(mock_engine)


def test_template_attrs():
    """
    _TemplateModelBase, TemplatePatchModel and OrderTemplateBase are the same
    OrderTemplate and TemplateModel are the same

    """
    sql_base = [
        name
        for name in inspect.signature(template_db._TemplateModelBase).parameters.keys()
    ]
    pydantic_patch = [
        name for name in inspect.signature(schemas.TemplatePatchModel).parameters.keys()
    ]
    pydantic_create = [
        name
        for name in inspect.signature(schemas.TemplateCreateModel).parameters.keys()
    ]
    domain_base = [
        name
        for name in inspect.signature(
            order_templates.OrderTemplateBase
        ).parameters.keys()
    ]
    template_sql_model = [
        name for name in inspect.signature(template_db.TemplateModel).parameters.keys()
    ]
    template_domain_model = [
        name
        for name in inspect.signature(order_templates.OrderTemplate).parameters.keys()
    ]
    assert sql_base == pydantic_patch == domain_base == pydantic_create
    assert template_sql_model == template_domain_model


class TestTemplateService:
    def test_get_template(self, stub_uow):
        template_obj = GetOrderTemplate.execute(uow=stub_uow, template_id="foo")
        assert template_obj is None

    def test_list_templates(self, stub_uow):
        template_list = ListOrderTemplates.execute(uow=stub_uow)
        assert template_list == []

    def test_save_template(self, stub_uow, stub_template_data, make_template):
        template = make_template(stub_template_data)
        template_saver = SaveNewOrderTemplate.execute(uow=stub_uow, obj=template)
        assert template_saver.name == stub_template_data["name"]
        assert template_saver.agent == stub_template_data["agent"]
        assert template_saver.blanket_po == stub_template_data["blanket_po"]

    @pytest.mark.parametrize(
        "id, name, agent",
        [
            (1, "Foo Template", "user1"),
            (2, "Bar Template", "user1"),
            (3, "Baz Template", "user2"),
            (4, "Qux Template", "user3"),
        ],
    )
    def test_save_template_check(self, id, name, agent, make_template, stub_uow):
        template = make_template(
            data={
                "id": id,
                "name": name,
                "agent": agent,
                "country": "xxu",
                "primary_matchpoint": "isbn",
            }
        )
        SaveNewOrderTemplate.execute(uow=stub_uow, obj=template)
        saved_template = GetOrderTemplate.execute(uow=stub_uow, template_id=id)
        assert saved_template.__dict__ == template.model_dump()

    def test_update_template(self, make_template, stub_uow):
        template = make_template(
            data={
                "id": "1",
                "name": "foo",
                "agent": "bar",
                "country": "xxu",
                "primary_matchpoint": "isbn",
            }
        )
        template_patch = schemas.TemplatePatchModel(
            primary_matchpoint="upc", lang="eng"
        )
        SaveNewOrderTemplate.execute(uow=stub_uow, obj=template)
        original_template = GetOrderTemplate.execute(uow=stub_uow, template_id="1")
        updated_template = UpdateOrderTemplate.execute(
            uow=stub_uow, template_id="1", obj=template_patch
        )
        no_update = UpdateOrderTemplate.execute(
            uow=stub_uow, template_id="2", obj=template_patch
        )
        assert updated_template.lang != original_template.lang
        assert (
            updated_template.primary_matchpoint != original_template.primary_matchpoint
        )
        assert updated_template.id == original_template.id
        assert no_update is None
