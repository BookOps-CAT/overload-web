import pytest
from sqlalchemy import text

from overload_web.domain import model
from overload_web.infrastructure import repository


def test_SqlAlchemyTemplateRepository(test_sql_session):
    repo = repository.SqlAlchemyTemplateRepository(session=test_sql_session)
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
    repo = repository.SqlAlchemyTemplateRepository(session=test_sql_session)
    template = make_template(
        data={"id": id, "name": name, "agent": agent, "country": "xxu"},
        matchpoints={"primary": "isbn"},
    )
    repo.save(template)
    saved_template = repo.get(id=id)
    assert saved_template == template


def test_save_and_update_template(test_sql_session, make_template):
    repo = repository.SqlAlchemyTemplateRepository(session=test_sql_session)
    template = make_template(
        data={"id": 1, "name": "Foo Template", "agent": "user1", "country": "xxu"},
        matchpoints={"primary": "isbn"},
    )
    repo.save(template)
    saved_template = repo.get(id=1)
    assert saved_template.lang is None
    template.lang = "eng"
    repo.save(template)
    updated_template = repo.get(id=1)
    assert updated_template.lang == "eng"


def test_SqlAlchemyVendorFileRepository(test_sql_session):
    repo = repository.SqlAlchemyVendorFileRepository(session=test_sql_session)
    assert hasattr(repo, "session")


@pytest.mark.parametrize("library", ["nypl", "bpl"])
def test_save_vendor_file(test_sql_session, make_vendor_file, library):
    repo = repository.SqlAlchemyVendorFileRepository(session=test_sql_session)
    file = make_vendor_file(
        data={"id": 1, "file_name": "foo.mrc", "library": library, "content": b""}
    )
    repo.save(file)
    saved_file = repo.get(id=1)
    assert saved_file == file


def test_template_mappers(test_sql_session, make_template):
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
    assert test_sql_session.query(model.Template).all() == expected


@pytest.mark.parametrize("library", ["nypl"])
def test_vendor_file_mappers(test_sql_session, make_vendor_file, library):
    test_sql_session.execute(
        text(
            "INSERT INTO vendor_files (id, library, file_name, content)"
            "VALUES"
            '("1", "nypl", "foo.mrc", ""),'
            '("2", "nypl", "bar.mrc", "");'
        )
    )
    file_1 = make_vendor_file(
        data={"id": 1, "file_name": "foo.mrc", "library": library, "content": ""}
    )
    file_2 = make_vendor_file(
        data={"id": 2, "file_name": "bar.mrc", "library": library, "content": ""}
    )
    expected = [file_1, file_2]
    assert test_sql_session.query(model.VendorFile).all() == expected
