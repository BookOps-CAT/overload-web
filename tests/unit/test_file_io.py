import os

import pytest
import yaml
from file_retriever import Client

from overload_web.domain import models
from overload_web.infrastructure import local_io, sftp


@pytest.mark.livetest
class TestLiveLocalFiles:
    test_dir = "tests/unit/test_dir"

    @pytest.fixture
    def setup_dirs(self):
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        if not os.path.exists(os.path.join(self.test_dir, "test_bib.mrc")):
            with open(os.path.join(self.test_dir, "test_bib.mrc"), "wb") as f:
                f.write(b"02741pam  a2200445 a 4500")
        yield
        if os.path.exists(self.test_dir):
            for file in os.listdir(self.test_dir):
                os.remove(os.path.join(self.test_dir, file))
            os.rmdir(self.test_dir)

    def test_load(self, setup_dirs):
        loader = local_io.LocalFileLoader()
        loaded_file = loader.load("test_bib.mrc", dir=self.test_dir)
        assert loaded_file.content[0:8] == b"02741pam"

    def test_list(self, setup_dirs):
        loader = local_io.LocalFileLoader()
        files = loader.list(dir=self.test_dir)
        assert len(files) == 1
        assert files[0] == "test_bib.mrc"

    def test_write(self, setup_dirs):
        writer = local_ioLocalFileWriter()
        file = models.files.VendorFile(
            id="foo.mrc", file_name="foo.mrc", content=b"Test content"
        )
        new_file = writer.write(file=file, dir=self.test_dir)
        assert new_file == os.path.join(self.test_dir, "foo.mrc")
        assert "foo.mrc" in os.listdir(self.test_dir)
        assert "Test content".encode() in open(new_file, "rb").read()


@pytest.mark.livetest
class TestSFTPFiles:
    test_dir = "NSDROP/vendor_records/test"

    @pytest.fixture(scope="class")
    def live_test_client(self):
        with open(
            os.path.join(os.environ["USERPROFILE"], ".cred/.overload/live_creds.yaml")
        ) as cred_file:
            data = yaml.safe_load(cred_file)
            for k, v in data.items():
                os.environ[k] = v
        client = Client(
            name="NSDROP",
            username=os.environ["NSDROP_USER"],
            host=os.environ["NSDROP_HOST"],
            port=os.environ["NSDROP_PORT"],
            password=os.environ["NSDROP_PASSWORD"],
        )
        yield client
        for file in client.session.connection.listdir():
            client.session.connection.remove(file)
        os.environ.update(
            {
                "NSDROP_USER": "foo",
                "NSDROP_PASSWORD": "bar",
                "NSDROP_HOST": "sftp.baz.com",
                "NSDROP_PORT": "22",
            }
        )

    def test_write(self, live_test_client):
        writer = sftp.SFTPFileWriter(client=live_test_client)
        outfile = writer.write(
            file=models.files.VendorFile(
                id="test_bib.mrc",
                file_name="test_bib.mrc",
                content=b"02741pam  a2200445 a 4500",
            ),
            dir=self.test_dir,
        )
        live_test_client.session.connection.chdir(None)
        assert outfile == "test_bib.mrc"

    def test_list(self, live_test_client):
        loader = sftp.SFTPFileLoader(client=live_test_client)
        file_list = loader.list(dir=self.test_dir)
        assert len(file_list) == 1
        assert file_list[0] == "test_bib.mrc"

    def test_load(self, live_test_client):
        loader = sftp.SFTPFileLoader(client=live_test_client)
        file = loader.load(name="test_bib.mrc", dir=self.test_dir)
        assert file.file_name == "test_bib.mrc"
        assert file.content[0:8] == b"02741pam"
