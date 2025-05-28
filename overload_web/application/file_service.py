"""Application service functions for matching bib records and applying templates.

Functions coordinate interactions between domain models, infrastructure adapters,
and presentation layer.
"""

from __future__ import annotations

import logging

from overload_web.infrastructure import file_loaders

logger = logging.getLogger(__name__)


class FileService:
    def __init__(self, loader: file_loaders.FileLoaderProtocol) -> None:
        self.loader = loader

    def load_file(self, file_name: str, dir: str) -> bytes:
        return self.loader.get(file_name=file_name, dir=dir)
