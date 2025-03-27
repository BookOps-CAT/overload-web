from __future__ import annotations

from typing import BinaryIO, Generator, Optional, Sequence

from bookops_marc import Bib, SierraBibReader
from bookops_marc.models import Field
from bookops_marc.models import Order as BookopsMarcOrder


class OverloadBib(Bib):

    @property
    def orders(self) -> Sequence[OverloadOrder]:
        orders = []
        for field in self.fields:
            if field.tag == "960":
                try:
                    following_field = self.fields[self.pos]
                except IndexError:
                    following_field = None
                orders.append(OverloadOrder(field, following_field))
        return orders

    @classmethod
    def from_bookops_bib(cls, bib: Bib) -> OverloadBib:
        bib_attrs = {"leader": bib.leader, "fields": bib.fields, "library": bib.library}
        overload_bib = OverloadBib()
        for k, v in bib_attrs.items():
            setattr(overload_bib, k, v)
        return overload_bib


class OverloadOrder(BookopsMarcOrder):
    def __init__(self, field: Field, following_field: Optional[Field] = None) -> None:
        super().__init__(field, following_field)

    def _get_subfield_from_following_field(self, code: str) -> Optional[str]:
        if self._following_field and self._following_field.tag == "961":
            subfield = self._following_field.get(code, None)
            return subfield
        else:
            return None

    @property
    def audience(self) -> Optional[str]:
        return self._field.get("f", None)

    @property
    def blanket_po(self) -> Optional[str]:
        return self._get_subfield_from_following_field("m")

    @property
    def country(self) -> Optional[str]:
        return self._field.get("x", None)

    @property
    def fund(self) -> Optional[str]:
        return self._field.get("u", None)

    @property
    def internal_note(self) -> Optional[str]:
        return self._get_subfield_from_following_field("d")

    @property
    def order_type(self) -> Optional[str]:
        return self._field.get("i", None)

    @property
    def price(self) -> Optional[str]:
        return self._field.get("s", None)

    @property
    def selector(self) -> Optional[str]:
        return self._field.get("c", None)

    @property
    def source(self) -> Optional[str]:
        return self._field.get("e", None)

    @property
    def status(self) -> Optional[str]:
        return self._field.get("m", None)

    @property
    def vendor_code(self) -> Optional[str]:
        return self._field.get("v", None)

    @property
    def var_field_isbn(self) -> Optional[str]:
        return self._get_subfield_from_following_field("l")

    @property
    def selector_note(self) -> Optional[str]:
        return self._get_subfield_from_following_field("f")

    @property
    def vendor_title_no(self) -> Optional[str]:
        return self._get_subfield_from_following_field("i")


def read_marc_file(
    marc_file: BinaryIO, library: str
) -> Generator[OverloadBib, None, None]:
    reader = SierraBibReader(marc_file, library=library, hide_utf8_warnings=True)
    for record in reader:
        yield OverloadBib.from_bookops_bib(record)
