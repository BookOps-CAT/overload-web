import pytest
from sqlmodel import Session, SQLModel, create_engine

from overload_web.order_templates.infrastructure import repository, tables


@pytest.fixture
def test_sql_session():
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def make_template():
    def _make_template(data):
        template = tables.TemplateTable(**data)
        return template

    return _make_template


class TestTemplateService:
    @pytest.fixture
    def service(self, test_sql_session):
        return repository.SqlModelRepository(session=test_sql_session)

    def test_SqlModelRepository(self, test_sql_session):
        repo = repository.SqlModelRepository(session=test_sql_session)
        assert hasattr(repo, "session")

    def test_get_template(self, service):
        template_obj = service.get(id="foo")
        assert template_obj is None

    def test_list_templates(self, service):
        template_list = service.list()
        assert template_list == []

    def test_save_template(self, service, fake_template_data, make_template):
        template = make_template(fake_template_data)
        template_saver = service.save(obj=template)
        assert template_saver.name == fake_template_data["name"]
        assert template_saver.agent == fake_template_data["agent"]
        assert template_saver.blanket_po == fake_template_data["blanket_po"]

    @pytest.mark.parametrize(
        "id, name, agent",
        [
            (1, "Foo Template", "user1"),
            (2, "Bar Template", "user1"),
            (3, "Baz Template", "user2"),
            (4, "Qux Template", "user3"),
        ],
    )
    def test_save_template_check(self, id, name, agent, make_template, service):
        template = make_template(
            data={
                "id": id,
                "name": name,
                "agent": agent,
                "country": "xxu",
                "primary_matchpoint": "isbn",
            },
        )
        service.save(template)
        saved_template = service.get(id=id)
        assert saved_template.__dict__ == template.model_dump()
