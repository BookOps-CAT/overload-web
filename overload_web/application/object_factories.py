from __future__ import annotations

from typing import Any, Dict, Generic, TypeVar, Union

from overload_web.application import marc_adapters
from overload_web.domain import model

T = TypeVar("T")  # input object
U = TypeVar("U")  # domain model object
V = TypeVar("V")  # dictionary object


class GenericFactory(Generic[T, U, V]):
    def to_dict(self, input_object: T) -> V:
        raise NotImplementedError("Subclasses should implement this method.")

    def to_domain(self, input_object: T) -> U:
        raise NotImplementedError("Subclasses should implement this method.")


class OrderFactory(
    GenericFactory[
        Union[model.Order, marc_adapters.OverloadOrder], model.Order, Dict[str, Any]
    ]
):
    def to_dict(
        self, order: Union[model.Order, marc_adapters.OverloadOrder]
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "audience": order.audience,
            "blanket_po": order.blanket_po,
            "copies": order.copies,
            "country": order.country,
            "fund": order.fund,
            "internal_note": order.internal_note,
            "lang": order.lang,
            "order_type": order.order_type,
            "price": order.price,
            "selector": order.selector,
            "selector_note": order.selector_note,
            "source": order.source,
            "status": order.status,
            "var_field_isbn": order.var_field_isbn,
            "vendor_code": order.vendor_code,
            "vendor_title_no": order.vendor_title_no,
        }
        if isinstance(order, marc_adapters.OverloadOrder):
            data["create_date"] = order.created
            data["format"] = order.form
            data["locations"] = order.locs
            data["vendor_notes"] = order.venNotes
        else:
            data["create_date"] = order.create_date
            data["format"] = order.format
            data["locations"] = order.locations
            data["vendor_notes"] = order.vendor_notes
        return data

    def to_domain(
        self, order: Union[model.Order, marc_adapters.OverloadOrder]
    ) -> model.Order:
        return model.Order(**self.to_dict(order=order))


class BibFactory(
    GenericFactory[
        Union[model.DomainBib, marc_adapters.OverloadBib],
        model.DomainBib,
        Dict[str, Any],
    ]
):
    order_factory = OrderFactory()

    def to_dict(
        self, bib: Union[model.DomainBib, marc_adapters.OverloadBib]
    ) -> Dict[str, Any]:
        orders = [self.order_factory.to_dict(i) for i in bib.orders]
        if isinstance(bib, marc_adapters.OverloadBib):
            return {
                "library": bib.library,
                "orders": orders,
                "bib_id": bib.sierra_bib_id,
                "isbn": bib.isbn,
                "oclc_number": list(bib.oclc_nos.values()),
                "upc": bib.upc_number,
            }
        return {
            "library": bib.library,
            "orders": orders,
            "bib_id": bib.bib_id,
            "isbn": bib.isbn,
            "oclc_number": bib.oclc_number,
            "upc": bib.upc,
        }

    def to_domain(
        self, bib: Union[model.DomainBib, marc_adapters.OverloadBib]
    ) -> model.DomainBib:
        bib_data = self.to_dict(bib=bib)
        orders = [model.Order(**i) for i in bib_data["orders"]]
        bib_data["orders"] = orders
        return model.DomainBib(**bib_data)
