import os
from typing import Any, Optional

from file_retriever import Client

from overload_web.application import dto, services
from overload_web.domain import logic, models, protocols
from overload_web.infrastructure.bibs import marc, sierra
from overload_web.infrastructure.file_io import local, sftp


def get_record_processor(
    library: str,
    matchpoints: list[str],
    template: models.templates.Template | dict[str, Any],
) -> services.records.RecordProcessingService:
    fetcher: protocols.bibs.BibFetcher = sierra.SierraBibFetcher(library=library)
    parser: protocols.bibs.MarcTransformer[dto.bib.BibDTO] = (
        marc.BookopsMarcTransformer(library=models.bibs.LibrarySystem(library))
    )
    matcher = logic.bibs.BibMatcher(fetcher=fetcher, matchpoints=matchpoints)
    return services.records.RecordProcessingService(
        matcher=matcher, parser=parser, template=template
    )


def create_file_service(
    remote: bool, vendor: Optional[str]
) -> services.file.FileTransferService:
    loader: protocols.file_io.FileLoader
    writer: protocols.file_io.FileWriter
    if remote and not vendor:
        raise ValueError("`vendor` arg required for remote files.")
    elif remote and vendor:
        client = Client(
            name=vendor.upper(),
            username=os.environ[f"{vendor.upper()}_USER"],
            password=os.environ[f"{vendor.upper()}_PASSWORD"],
            host=os.environ[f"{vendor.upper()}_HOST"],
            port=os.environ[f"{vendor.upper()}_PORT"],
        )
        loader = sftp.SFTPFileLoader(client=client)
        writer = sftp.SFTPFileWriter(client=client)
    else:
        loader = local.LocalFileLoader()
        writer = local.LocalFileWriter()
    return services.file.FileTransferService(loader=loader, writer=writer)
