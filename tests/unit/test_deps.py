import pytest
from sqlmodel import Session, create_engine

from overload_web.presentation import deps


@pytest.fixture
def mock_storage(monkeypatch):
    def mock_mkdir(*args, **kwargs):
        pass

    monkeypatch.setattr("pathlib.Path.mkdir", mock_mkdir)


class TestDeps:
    def test_get_session(self):
        engine = create_engine("sqlite:///:memory:")
        deps.create_db_and_tables(engine)
        session = deps.get_session(engine)
        assert isinstance(next(session), Session)
        session.close()
        engine.dispose()

    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_get_fetcher(self, mock_sierra_session, library):
        fetcher_generator = deps.get_fetcher(library=library)
        fetcher = next(fetcher_generator)
        assert str(fetcher.__class__.__name__) == "SierraBibFetcher"

    def test_local_file_storage(self, mock_storage):
        storage = deps.local_file_storage()
        assert str(storage.base_path) == "temp\\uploads"

    def test_remote_file_retriever(self, mock_sftp_client):
        retriever_generator = deps.remote_file_retriever(vendor="foo")
        retriever = next(retriever_generator)
        assert hasattr(retriever, "client")
