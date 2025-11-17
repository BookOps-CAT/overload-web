import pytest

from overload_web.application import template_service
from overload_web.order_templates.infrastructure import repository


class TestTemplateService:
    @pytest.fixture
    def service(self, test_sql_session):
        return template_service.OrderTemplateService(
            repo=repository.SqlModelRepository(session=test_sql_session)
        )

    def test_get_template(self, service):
        template_obj = service.get_template(template_id="foo")
        assert template_obj is None

    def test_list_templates(self, service):
        template_list = service.list_templates()
        assert template_list == []

    def test_save_template(self, service, template_data, make_template):
        template = make_template(template_data)
        template_saver = service.save_template(obj=template)
        assert template_saver.name == template_data["name"]
        assert template_saver.agent == template_data["agent"]
        assert template_saver.blanket_po == template_data["blanket_po"]
