import pytest

from overload_web.application import services


class TestTemplateService:
    @pytest.fixture
    def service(self, test_sql_session):
        return services.template.TemplateService(session=test_sql_session)

    def test_get_template(self, service):
        template_obj = service.get_template(template_id="foo")
        assert template_obj is None

    def test_list_templates(self, service):
        template_list = service.list_templates()
        assert template_list == []

    def test_save_template(self, service, template_data, make_template):
        template_data.update(
            {"name": "Foo", "agent": "Bar", "primary_matchpoint": "isbn"}
        )
        template = make_template(template_data)
        template_saver = service.save_template(obj=template)
        assert template_saver.name == template_data["name"]
        assert template_saver.agent == template_data["agent"]
        assert template_saver.blanket_po == template_data["blanket_po"]

    def test_save_template_no_name(self, service, template_data, make_template):
        template_data.update({"primary_matchpoint": "isbn"})
        template = make_template(template_data)
        with pytest.raises(ValueError) as exc:
            service.save_template(obj=template)
        assert str(exc.value) == "Templates must have a name before being saved."

    def test_save_template_no_agent(self, service, template_data, make_template):
        template_data.update({"name": "Foo", "primary_matchpoint": "isbn"})
        template = make_template(template_data)
        with pytest.raises(ValueError) as exc:
            service.save_template(obj=template)
        assert str(exc.value) == "Templates must have an agent before being saved."
