import inspect

import pytest

from overload_web.application.pvf.template_handling import (
    GetOrderTemplate,
    ListOrderTemplates,
    SaveNewOrderTemplate,
    UpdateOrderTemplate,
)
from overload_web.domain.pvf import order_templates
from overload_web.infrastructure import tables
from overload_web.presentation import schemas


def test_template_attrs():
    """
    TemplateUpdateModel, TemplatePatchModel and OrderTemplateBase are the same
    OrderTemplate and TemplateModel are the same

    """
    sql_base = [
        name for name in inspect.signature(tables.TemplateUpdateModel).parameters.keys()
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
        name for name in inspect.signature(tables.TemplateModel).parameters.keys()
    ]
    template_domain_model = [
        name
        for name in inspect.signature(order_templates.OrderTemplate).parameters.keys()
    ]
    assert sql_base == pydantic_patch == domain_base == pydantic_create
    assert template_sql_model == template_domain_model


class TestTemplateService:
    def test_get_template(self, fake_uow):
        template_obj = GetOrderTemplate.execute(uow=fake_uow, template_id=1)
        assert template_obj is None

    def test_list_templates(self, fake_uow):
        template_list = ListOrderTemplates.execute(uow=fake_uow)
        assert template_list == []

    def test_save_template(self, fake_uow):
        template = tables.TemplateModel(name="Foo", agent="Bar", blanket_po=None, id=1)
        template_saver = SaveNewOrderTemplate.execute(uow=fake_uow, obj=template)
        assert template_saver.name == "Foo"
        assert template_saver.agent == "Bar"
        assert template_saver.blanket_po is None

    @pytest.mark.parametrize(
        "id, name, agent",
        [
            (1, "Foo Template", "user1"),
            (2, "Bar Template", "user1"),
            (3, "Baz Template", "user2"),
            (4, "Qux Template", "user3"),
        ],
    )
    def test_save_template_check(self, id, name, agent, fake_uow):
        template = tables.TemplateModel(
            id=id, name=name, agent=agent, country="xxu", primary_matchpoint="isbn"
        )
        SaveNewOrderTemplate.execute(uow=fake_uow, obj=template)
        saved_template = GetOrderTemplate.execute(uow=fake_uow, template_id=id)
        assert saved_template.__dict__ == template.model_dump()

    def test_update_template(self, fake_uow):
        template = tables.TemplateModel(
            id=1, name="foo", agent="bar", country="xxu", primary_matchpoint="isbn"
        )
        template_patch = schemas.TemplatePatchModel(
            primary_matchpoint="upc", lang="eng"
        )
        SaveNewOrderTemplate.execute(uow=fake_uow, obj=template)
        original_template = GetOrderTemplate.execute(uow=fake_uow, template_id=1)
        updated_template = UpdateOrderTemplate.execute(
            uow=fake_uow, template_id=1, obj=template_patch
        )
        no_update = UpdateOrderTemplate.execute(
            uow=fake_uow, template_id="10", obj=template_patch
        )
        assert updated_template.id == original_template.id
        assert updated_template.lang != original_template.lang
        assert (
            updated_template.primary_matchpoint != original_template.primary_matchpoint
        )
        assert updated_template.id == original_template.id
        assert no_update is None
