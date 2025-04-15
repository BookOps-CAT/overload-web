import datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import clear_mappers, sessionmaker

from overload_web.adapters import orm, repository
from overload_web.domain import model


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
def test_SqlAlchemyRepository_get_save(id, name, agent, session, template_data):
    repo = repository.SqlAlchemyRepository(session=session)
    template_data["id"], template_data["name"], template_data["agent"] = id, name, agent
    template_data["create_date"] = datetime.date(2024, 1, 1)
    template = model.Template(**template_data)
    assert isinstance(template, model.Template)
    repo.save(template)
    saved_template = repo.get(id=id)
    assert saved_template == model.Template(
        id=id,
        name=name,
        agent=agent,
        audience="a",
        blanket_po=None,
        copies="5",
        country="xxu",
        create_date=datetime.date(2024, 1, 1),
        format="a",
        fund="10001adbk",
        internal_note="foo",
        lang="spa",
        order_type="p",
        price="$20.00",
        selector="b",
        selector_note=None,
        source="d",
        status="o",
        var_field_isbn=None,
        vendor_code="0049",
        vendor_notes="bar",
        vendor_title_no=None,
        primary_matchpoint="isbn",
        secondary_matchpoint=None,
        tertiary_matchpoint=None,
    )


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
            primary_matchpoint="isbn",
        ),
        model.Template(
            id=2,
            name="Bar Template",
            agent="user2",
            vendor_code="BAR",
            primary_matchpoint="upc",
        ),
        model.Template(
            id=3,
            name="Baz Template",
            agent="user1",
            vendor_code="BAZ",
            primary_matchpoint="isbn",
        ),
    ]
    assert session.query(model.Template).all() == expected
