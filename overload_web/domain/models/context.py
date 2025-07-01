"""Define the context within which application services are called.

Meaning that this defines the library system and collection
"""

from typing import Any

from overload_web import constants
from overload_web.domain import models


class SessionContext:
    def __init__(
        self,
        library: models.bibs.LibrarySystem,
        collection: models.bibs.Collection | None,
        vendor: str | None,
    ) -> None:
        self.library = library
        self.collection = collection
        self.vendor = vendor
        self.vendor_data: dict[str, Any] = self._get_vendor_data()

    def _get_vendor_data(self) -> dict[str, Any]:
        vendor_data = {}
        vendor_rules = constants.VENDOR_RULES.get(str(self.library), {})
        if self.vendor and vendor_rules:
            data = vendor_rules.get(self.vendor.upper(), {})
            vendor_data.update({k: v for k, v in data.items()})
        return vendor_data
