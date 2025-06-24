from overload_web.domain import models, protocols


class FileService:
    def __init__(
        self, loader: protocols.file_io.FileLoader, writer: protocols.file_io.FileWriter
    ):
        self.loader = loader
        self.writer = writer

    def list_files(self) -> list[str]:
        return self.loader.list()

    def load_file(self, name: str) -> models.files.VendorFile:
        return self.loader.load(name=name)

    def write_marc_file(self, file: models.files.VendorFile) -> str:
        return self.writer.write(file)
