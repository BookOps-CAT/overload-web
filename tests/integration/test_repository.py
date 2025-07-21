import pytest
from sqlalchemy import text

from overload_web.domain import models
from overload_web.infrastructure.repositories import repository


@pytest.fixture
def make_template():
    def _make_template(data, matchpoints):
        template = models.templates.Template(**data)
        matchpoints = models.templates.Matchpoints(**matchpoints)
        template.matchpoints = matchpoints
        return template

    return _make_template


def test_SqlAlchemyRepository(test_sql_session):
    repo = repository.SqlAlchemyRepository(session=test_sql_session)
    assert hasattr(repo, "session")


@pytest.mark.parametrize(
    "id, name, agent",
    [
        (1, "Foo Template", "user1"),
        (2, "Bar Template", "user1"),
        (3, "Baz Template", "user2"),
        (4, "Qux Template", "user3"),
    ],
)
def test_save_template(id, name, agent, test_sql_session, make_template):
    repo = repository.SqlAlchemyRepository(session=test_sql_session)
    template = make_template(
        data={"id": id, "name": name, "agent": agent, "country": "xxu"},
        matchpoints={"primary": "isbn"},
    )
    repo.save(template)
    saved_template = repo.get(id=id)
    assert saved_template == template


def test_save_and_update_template(test_sql_session, make_template):
    repo = repository.SqlAlchemyRepository(session=test_sql_session)
    template = make_template(
        data={"id": 1, "name": "Foo Template", "agent": "user1", "country": "xxu"},
        matchpoints={"primary": "isbn"},
    )
    repo.save(template)
    saved_template = repo.get(id=1)
    assert saved_template.lang is None
    template.lang = "eng"
    repo.save(template)
    updated_template = repo.list()
    assert updated_template[0].lang == "eng"


def test_mappers(test_sql_session, make_template):
    test_sql_session.execute(
        text(
            "INSERT INTO templates (id, name, agent, vendor_code, primary_matchpoint)"
            "VALUES"
            '("1", "Foo Template", "user1", "FOO", "isbn"),'
            '("2", "Bar Template", "user2", "BAR", "upc"),'
            '("3", "Baz Template", "user1", "BAZ", "isbn");'
        )
    )
    template_1 = make_template(
        data={"id": 1, "name": "Foo Template", "agent": "user1", "vendor_code": "FOO"},
        matchpoints={"primary": "isbn"},
    )
    template_2 = make_template(
        data={"id": 2, "name": "Bar Template", "agent": "user2", "vendor_code": "BAR"},
        matchpoints={"primary": "upc"},
    )
    template_3 = make_template(
        data={"id": 3, "name": "Baz Template", "agent": "user1", "vendor_code": "BAZ"},
        matchpoints={"primary": "isbn"},
    )
    expected = [template_1, template_2, template_3]
    assert test_sql_session.query(models.templates.Template).all() == expected
