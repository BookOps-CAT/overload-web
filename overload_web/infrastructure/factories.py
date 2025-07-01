from overload_web.application import services
from overload_web.infrastructure.file_io import local, sftp


def create_local_file_service() -> services.file.FileTransferService:
    return services.file.FileTransferService(
        loader=local.LocalFileLoader(),
        writer=local.LocalFileWriter(),
    )


def create_remote_file_service(vendor: str) -> services.file.FileTransferService:
    return services.file.FileTransferService(
        loader=sftp.SFTPFileLoader.create_loader_for_vendor(vendor=vendor),
        writer=sftp.SFTPFileWriter.create_writer_for_vendor(vendor=vendor),
    )
