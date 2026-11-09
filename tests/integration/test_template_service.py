"""Test template handling application services."""

import inspect

import pytest

from overload_web.application.pvf import queries
from overload_web.domain.pvf import commands, order_templates
from overload_web.infrastructure import tables
from overload_web.presentation import schemas


def test_template_attrs():
    """TemplateUpdateModel, TemplateDataModel and OrderTemplateBase are the same
    OrderTemplate and TemplateModel are the same.

    """
    sql_base = list(inspect.signature(tables.TemplateUpdateModel).parameters.keys())
    pydantic_patch = list(
        inspect.signature(schemas.TemplateDataModel).parameters.keys()
    )
    pydantic_create = list(
        inspect.signature(schemas.TemplateCreateModel).parameters.keys()
    )
    domain_base = list(
        inspect.signature(order_templates.OrderTemplateBase).parameters.keys()
    )
    template_sql_model = list(inspect.signature(tables.TemplateModel).parameters.keys())
    template_domain_model = list(
        inspect.signature(order_templates.OrderTemplate).parameters.keys()
    )
    assert sql_base == pydantic_patch == domain_base == pydantic_create
    assert template_sql_model == template_domain_model


class TestTemplateService:
    def test_get_template(self, fake_uow):
        template_obj = queries.get_order_template(uow=fake_uow, template_id=1)
        assert template_obj is None

    def test_list_templates(self, fake_uow):
        template_list = queries.list_order_templates(uow=fake_uow, offset=0, limit=20)
        assert template_list == []

    def test_create_order_template(self, stub_order_level_manager, caplog):
        bus = stub_order_level_manager.bus
        bus.send(
            commands.CreateOrderTemplate(
                data=tables.TemplateModel(
                    name="Foo", agent="Bar", blanket_po=None, id=1
                )
            )
        )
        assert len(caplog.records) == 2
        assert "Handling command: CreateOrderTemplate" == caplog.records[0].msg
        assert caplog.records[1].msg.startswith("New template saved to database: ")

    @pytest.mark.parametrize(
        "id, name, agent",
        [
            (1, "Foo Template", "user1"),
            (2, "Bar Template", "user1"),
            (3, "Baz Template", "user2"),
            (4, "Qux Template", "user3"),
        ],
    )
    def test_create_order_template_check(
        self, id, name, agent, stub_order_level_manager
    ):
        template = tables.TemplateModel(
            id=id, name=name, agent=agent, country="xxu", primary_matchpoint="isbn"
        )
        bus = stub_order_level_manager.bus
        uow = stub_order_level_manager.uow
        bus.send(commands.CreateOrderTemplate(data=template))
        saved_template = queries.get_order_template(template_id=id, uow=uow)
        assert saved_template.__dict__ == template.model_dump()

    def test_update_template(self, stub_order_level_manager):
        template = tables.TemplateModel(
            id=1, name="foo", agent="bar", country="xxu", primary_matchpoint="isbn"
        )
        template_patch = schemas.TemplateDataModel(primary_matchpoint="upc", lang="eng")
        bus = stub_order_level_manager.bus
        uow = stub_order_level_manager.uow
        bus.send(commands.CreateOrderTemplate(data=template))
        original_template = queries.get_order_template(template_id=1, uow=uow)
        bus.send(commands.UpdateOrderTemplate(template_id=1, data=template_patch))
        updated_template = queries.get_order_template(template_id=1, uow=uow)
        bus.send(commands.UpdateOrderTemplate(template_id=10, data=template_patch))
        no_update = queries.get_order_template(template_id=10, uow=uow)
        assert updated_template.id == original_template.id
        assert updated_template.lang != original_template.lang
        assert (
            updated_template.primary_matchpoint != original_template.primary_matchpoint
        )
        assert updated_template.id == original_template.id
        assert no_update is None


class TestOrderTemplateHandlers:
    def test_update_order_template(self, stub_order_level_manager, caplog):
        bus = stub_order_level_manager.bus
        bus.send(
            commands.UpdateOrderTemplate(
                template_id=1,
                data=tables.TemplateModel(
                    name="Foo", agent="Bar", blanket_po=None, id=1
                ),
            )
        )
        assert len(caplog.records) == 2
        assert "Handling command: UpdateOrderTemplate" == caplog.records[0].msg
        assert caplog.records[1].msg.startswith("Order template 1 updated: ")
