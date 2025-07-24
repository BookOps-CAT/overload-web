import pytest

from overload_web.infrastructure.repositories import repository


def test_SqlModelRepository(test_sql_session):
    repo = repository.SqlModelRepository(session=test_sql_session)
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
    repo = repository.SqlModelRepository(session=test_sql_session)
    template = make_template(
        data={
            "id": id,
            "name": name,
            "agent": agent,
            "country": "xxu",
            "primary_matchpoint": "isbn",
        },
    )
    repo.save(template)
    saved_template = repo.get(id=id)
    assert saved_template == template
