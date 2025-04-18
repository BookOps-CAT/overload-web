import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import clear_mappers, sessionmaker

from overload_web.domain import model
from overload_web.infrastructure import orm, repository


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    orm.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(in_memory_db):
    orm.start_mappers()
    yield sessionmaker(bind=in_memory_db)()
    clear_mappers()


def test_AbstractRepository():
    repository.AbstractRepository.__abstractmethods__ = set()
    session = repository.AbstractRepository()
    assert session.__dict__ == {}


def test_AbstractRepository_get():
    repo = repository.AbstractRepository()
    with pytest.raises(NotImplementedError) as exc:
        repo.get(id=1)
    assert str(exc.value) == ""


def test_AbstractRepository_save(template_data):
    repo = repository.AbstractRepository()
    template_data["id"], template_data["name"], template_data["agent"] = 1, "Foo", "Bar"
    with pytest.raises(NotImplementedError) as exc:
        repo.save(template=template_data)
    assert str(exc.value) == ""


def test_SqlAlchemyRepository(session):
    repo = repository.SqlAlchemyRepository(session=session)
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
def test_SqlAlchemyRepository_get_save(id, name, agent, session):
    repo = repository.SqlAlchemyRepository(session=session)
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


def test_mappers(session):
    session.execute(
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
    assert session.query(model.Template).all() == expected
