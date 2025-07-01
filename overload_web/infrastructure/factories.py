from typing import Optional

from overload_web.application import services
from overload_web.domain import protocols
from overload_web.infrastructure.file_io import local, sftp


def create_file_service(
    remote: bool, vendor: Optional[str]
) -> services.file.FileTransferService:
    loader: protocols.file_io.FileLoader
    writer: protocols.file_io.FileWriter
    if remote and not vendor:
        raise ValueError("`vendor` arg required for remote files.")
    elif remote and vendor:
        loader = sftp.SFTPFileLoader.create_loader_for_vendor(vendor=vendor)
        writer = sftp.SFTPFileWriter.create_writer_for_vendor(vendor=vendor)
    else:
        loader = local.LocalFileLoader()
        writer = local.LocalFileWriter()
    return services.file.FileTransferService(loader=loader, writer=writer)
