"""Test read queries used in application services."""

from overload_web.application.pvf import queries


class TestQueries:
    def test_get_detailed_report_data(self, fake_uow):
        out = queries.get_detailed_report_data(batch_id="1", uow=fake_uow)
        assert sorted(out[0].keys()) == sorted(
            [
                "vendor",
                "resource_id",
                "action",
                "target_bib_id",
                "updated_by_vendor",
                "target_title",
                "call_number_match",
                "call_number",
                "target_call_no",
                "duplicate_records",
                "mixed",
                "other",
            ]
        )

    def test_get_detailed_report_data_no_data(self, fake_uow_no_data):
        out = queries.get_detailed_report_data(batch_id="1", uow=fake_uow_no_data)
        assert out == []

    def test_get_order_template(self, fake_uow):
        template = queries.get_order_template(template_id=1, uow=fake_uow)
        assert template is not None
        assert template.id == 1

    def test_list_order_templates(self, fake_uow):
        templates = queries.list_order_templates(uow=fake_uow, offset=0, limit=20)
        assert len(templates) > 0

    def test_list_workflow_files(self, fake_uow):
        files = queries.list_workflow_files(uow=fake_uow, workflow_id="12345")
        assert len(files) > 0
        assert files[0]["workflow_id"] == "12345"
