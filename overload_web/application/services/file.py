from overload_web.domain import models, protocols


class FileTransferService:
    def __init__(
        self, loader: protocols.file_io.FileLoader, writer: protocols.file_io.FileWriter
    ):
        self.loader = loader
        self.writer = writer

    def list_files(self, dir: str) -> list[str]:
        return self.loader.list(dir=dir)

    def load_file(self, name: str, dir: str) -> models.files.VendorFile:
        return self.loader.load(name=name, dir=dir)

    def write_marc_file(self, file: models.files.VendorFile, dir: str) -> str:
        return self.writer.write(file=file, dir=dir)
