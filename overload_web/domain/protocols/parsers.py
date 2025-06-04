from typing import BinaryIO, Protocol, TypeVar, runtime_checkable

from overload_web.domain.models import bibs

T = TypeVar("T")


@runtime_checkable
class MarcTransformer(Protocol[T]):
    """
    Parse a binary object to MARC

    """

    library: bibs.LibrarySystem

    def parse(self, data: BinaryIO) -> list[T]: ...

    def serialize(self, records: list[T]) -> BinaryIO: ...
