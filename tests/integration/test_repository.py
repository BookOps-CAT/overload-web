import pytest
from sqlalchemy import text

from overload_web.domain import model
from overload_web.infrastructure import repository


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
def test_SqlAlchemyRepository_get_save(id, name, agent, test_sql_session):
    repo = repository.SqlAlchemyRepository(session=test_sql_session)
    template = model.Template(
        id=id,
        name=name,
        agent=agent,
        country="xxu",
        matchpoints=model.Matchpoints("isbn"),
    )
    assert isinstance(template, model.Template)
    repo.save(template)
    saved_template = repo.get(id=id)
    assert saved_template == template


def test_mappers(test_sql_session):
    test_sql_session.execute(
        text(
            "INSERT INTO templates (id, name, agent, vendor_code, primary_matchpoint)"
            "VALUES"
            '("1", "Foo Template", "user1", "FOO", "isbn"),'
            '("2", "Bar Template", "user2", "BAR", "upc"),'
            '("3", "Baz Template", "user1", "BAZ", "isbn");'
        )
    )
    expected = [
        model.Template(
            id=1,
            name="Foo Template",
            agent="user1",
            vendor_code="FOO",
            matchpoints=model.Matchpoints(primary="isbn"),
        ),
        model.Template(
            id=2,
            name="Bar Template",
            agent="user2",
            vendor_code="BAR",
            matchpoints=model.Matchpoints(primary="upc"),
        ),
        model.Template(
            id=3,
            name="Baz Template",
            agent="user1",
            vendor_code="BAZ",
            matchpoints=model.Matchpoints(primary="isbn"),
        ),
    ]
    assert test_sql_session.query(model.Template).all() == expected
