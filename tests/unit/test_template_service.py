import pytest
from sqlmodel import Session, SQLModel, create_engine

from overload_web.application.commands import (
    CreateOrderTemplate,
    GetOrderTemplate,
    ListOrderTemplates,
)
from overload_web.infrastructure.db import repository, tables


@pytest.fixture
def test_sql_session():
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    session.close()
    test_engine.dispose()


@pytest.fixture
def make_template():
    def _make_template(data):
        template = tables.TemplateTable(**data)
        return template

    return _make_template


class TestTemplateService:
    @pytest.fixture
    def repo(self, test_sql_session):
        return repository.SqlModelRepository(session=test_sql_session)

    def test_SqlModelRepository(self, test_sql_session):
        repo = repository.SqlModelRepository(session=test_sql_session)
        assert hasattr(repo, "session")

    def test_get_template(self, repo):
        template_obj = GetOrderTemplate.execute(repository=repo, template_id="foo")
        assert template_obj is None

    def test_list_templates(self, repo):
        template_list = ListOrderTemplates.execute(repository=repo)
        assert template_list == []

    def test_save_template(self, repo, fake_template_data, make_template):
        template = make_template(fake_template_data)
        template_saver = CreateOrderTemplate.execute(repository=repo, obj=template)
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
    def test_save_template_check(self, id, name, agent, make_template, repo):
        template = make_template(
            data={
                "id": id,
                "name": name,
                "agent": agent,
                "country": "xxu",
                "primary_matchpoint": "isbn",
            },
        )
        CreateOrderTemplate.execute(repository=repo, obj=template)
        saved_template = GetOrderTemplate.execute(repository=repo, template_id=id)
        assert saved_template.__dict__ == template.model_dump()
