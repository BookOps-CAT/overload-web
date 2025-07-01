"""Defines context used for record processing."""

from typing import Any

from overload_web import constants
from overload_web.domain import models


class SessionContext:
    """Encapsulates session-specific configuration for record processing operations."""

    def __init__(
        self,
        library: models.bibs.LibrarySystem,
        collection: models.bibs.Collection,
        vendor: str | None,
    ) -> None:
        """
        Initialize `SessionContext` object.

        Args:
            library:
                the library whose records are being processed as a `LibrarySystem` enum.
            collection:
                the collection whose records are being processed as a `Collection` enum.
            vendor:
                the vendor as a string used for custom logic.
        """
        self.library = library
        self.collection = collection
        self.vendor = vendor
        self.vendor_data: dict[str, Any] = self._get_vendor_data()

    def _get_vendor_data(self) -> dict[str, Any]:
        """
        Lookup and extract vendor-specific rules from configuration constants.

        Returns:
            vendor configuration as a dictionary
        """
        vendor_data = {}
        vendor_rules = constants.VENDOR_RULES.get(str(self.library), {})
        if self.vendor and vendor_rules:
            data = vendor_rules.get(self.vendor.upper(), {})
            vendor_data.update({k: v for k, v in data.items()})
        return vendor_data
