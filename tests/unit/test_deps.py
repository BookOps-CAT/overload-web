import pytest

from overload_web.presentation import deps


@pytest.fixture
def mock_storage(monkeypatch):
    def mock_mkdir(*args, **kwargs):
        pass

    monkeypatch.setattr("pathlib.Path.mkdir", mock_mkdir)


class TestDeps:
    @pytest.mark.parametrize("library", ["bpl", "nypl"])
    def test_get_fetcher(self, mock_sierra_session, library):
        fetcher = deps.get_fetcher(library=library)
        assert str(fetcher.__class__.__name__) == "SierraBibFetcher"

    def test_local_file_storage(self, mock_storage):
        storage = deps.local_file_storage()
        assert str(storage.base_path).startswith("temp")

    def test_remote_file_retriever(self, mock_sftp_client):
        retriever = deps.remote_file_retriever(vendor="foo")
        assert hasattr(retriever, "client")
