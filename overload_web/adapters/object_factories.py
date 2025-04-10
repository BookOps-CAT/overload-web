from __future__ import annotations

from typing import Any, BinaryIO, Dict, Generic, Optional, Sequence, TypeVar, Union

from overload_web.adapters import marc_adapters
from overload_web.api import schemas
from overload_web.domain import model

T = TypeVar("T")  # input object
U = TypeVar("U")  # domain model object
V = TypeVar("V")  # pydantic model object


class GenericFactory(Generic[T, U, V]):
    def to_domain(self, input_object: T) -> U:
        raise NotImplementedError("Subclasses should implement this method.")

    def to_pydantic(self, input_object: T) -> V:
        raise NotImplementedError("Subclasses should implement this method.")


class OrderFactory(
    GenericFactory[
        Union[model.Order, schemas.OrderModel, marc_adapters.OverloadOrder],
        model.Order,
        schemas.OrderModel,
    ]
):
    def _common_transforms(
        self,
        order: Union[model.Order, schemas.OrderModel, marc_adapters.OverloadOrder],
    ) -> dict:
        if isinstance(order, marc_adapters.OverloadOrder):
            return {
                "audience": order.audience,
                "blanket_po": order.blanket_po,
                "copies": order.copies,
                "country": order.country,
                "create_date": order.created,
                "format": order.form,
                "fund": order.fund,
                "internal_note": order.internal_note,
                "lang": order.lang,
                "locations": order.locs,
                "order_type": order.order_type,
                "price": order.price,
                "selector": order.selector,
                "selector_note": order.selector_note,
                "source": order.source,
                "status": order.status,
                "var_field_isbn": order.var_field_isbn,
                "vendor_code": order.vendor_code,
                "vendor_notes": order.venNotes,
                "vendor_title_no": order.vendor_title_no,
            }

        return {
            "audience": order.audience,
            "blanket_po": order.blanket_po,
            "copies": order.copies,
            "country": order.country,
            "create_date": order.create_date,
            "format": order.format,
            "fund": order.fund,
            "internal_note": order.internal_note,
            "lang": order.lang,
            "locations": order.locations,
            "order_type": order.order_type,
            "price": order.price,
            "selector": order.selector,
            "selector_note": order.selector_note,
            "source": order.source,
            "status": order.status,
            "var_field_isbn": order.var_field_isbn,
            "vendor_code": order.vendor_code,
            "vendor_notes": order.vendor_notes,
            "vendor_title_no": order.vendor_title_no,
        }

    def to_domain(
        self,
        order: Union[model.Order, schemas.OrderModel, marc_adapters.OverloadOrder],
    ) -> model.Order:
        return model.Order(**self._common_transforms(order=order))

    def to_pydantic(
        self,
        order: Union[model.Order, schemas.OrderModel, marc_adapters.OverloadOrder],
    ) -> schemas.OrderModel:
        return schemas.OrderModel(**self._common_transforms(order=order))


class BibFactory(
    GenericFactory[
        Union[
            model.DomainBib, schemas.BibModel, marc_adapters.OverloadBib, Dict[str, Any]
        ],
        model.DomainBib,
        schemas.BibModel,
    ]
):
    order_factory = OrderFactory()

    def _common_transforms(
        self,
        bib: Union[
            model.DomainBib, schemas.BibModel, marc_adapters.OverloadBib, Dict[str, Any]
        ],
        library: Optional[str] = "",
    ) -> dict:
        if isinstance(bib, marc_adapters.OverloadBib):
            order_factory = OrderFactory()
            return {
                "library": bib.library,
                "orders": [order_factory.to_domain(i) for i in bib.orders],
                "bib_id": bib.sierra_bib_id,
                "isbn": bib.isbn,
                "oclc_number": list(bib.oclc_nos.values()),
                "upc": bib.upc_number,
            }
        elif isinstance(bib, dict):
            return {
                "library": library,
                "orders": [],
                "bib_id": bib["id"],
                "isbn": bib.get("isbn"),
                "oclc_number": bib.get("oclc_number"),
                "upc": bib.get("upc"),
            }
        return {
            "library": bib.library,
            "orders": bib.orders,
            "bib_id": bib.bib_id,
            "isbn": bib.isbn,
            "oclc_number": bib.oclc_number,
            "upc": bib.upc,
        }

    def to_domain(
        self,
        bib: Union[
            model.DomainBib, schemas.BibModel, marc_adapters.OverloadBib, Dict[str, Any]
        ],
        library: Optional[str] = "",
    ) -> model.DomainBib:
        return model.DomainBib(**self._common_transforms(bib=bib, library=library))

    def to_pydantic(
        self,
        bib: Union[
            model.DomainBib, schemas.BibModel, marc_adapters.OverloadBib, Dict[str, Any]
        ],
        library: Optional[str] = "",
    ) -> schemas.BibModel:
        return schemas.BibModel(**self._common_transforms(bib=bib, library=library))

    def binary_to_domain_list(
        self, bib_data: BinaryIO, library: str
    ) -> Sequence[model.DomainBib]:
        marc_list = [i for i in marc_adapters.read_marc_file(bib_data, library=library)]
        return [model.DomainBib(**self._common_transforms(i)) for i in marc_list]

    def binary_to_pydantic_list(
        self, bib_data: BinaryIO, library: str
    ) -> Sequence[schemas.BibModel]:
        marc_list = [i for i in marc_adapters.read_marc_file(bib_data, library=library)]
        return [schemas.BibModel(**self._common_transforms(i)) for i in marc_list]


class TemplateFactory(
    GenericFactory[
        Union[model.Template, schemas.TemplateModel],
        model.Template,
        schemas.TemplateModel,
    ]
):
    def to_domain(
        self,
        template: Union[model.Template, schemas.TemplateModel],
    ) -> model.Template:
        return model.Template(
            audience=template.audience,
            blanket_po=template.blanket_po,
            copies=template.copies,
            country=template.country,
            create_date=template.create_date,
            format=template.format,
            fund=template.fund,
            internal_note=template.internal_note,
            lang=template.lang,
            order_type=template.order_type,
            price=template.price,
            selector=template.selector,
            selector_note=template.selector_note,
            source=template.source,
            status=template.status,
            var_field_isbn=template.var_field_isbn,
            vendor_code=template.vendor_code,
            vendor_notes=template.vendor_notes,
            vendor_title_no=template.vendor_title_no,
            primary_matchpoint=template.primary_matchpoint,
            secondary_matchpoint=template.secondary_matchpoint,
            tertiary_matchpoint=template.tertiary_matchpoint,
        )

    def to_pydantic(
        self,
        template: Union[model.Template, schemas.TemplateModel],
    ) -> schemas.TemplateModel:
        return schemas.TemplateModel(
            audience=template.audience,
            blanket_po=template.blanket_po,
            copies=template.copies,
            country=template.country,
            create_date=template.create_date,
            format=template.format,
            fund=template.fund,
            internal_note=template.internal_note,
            lang=template.lang,
            order_type=template.order_type,
            price=template.price,
            selector=template.selector,
            selector_note=template.selector_note,
            source=template.source,
            status=template.status,
            var_field_isbn=template.var_field_isbn,
            vendor_code=template.vendor_code,
            vendor_notes=template.vendor_notes,
            vendor_title_no=template.vendor_title_no,
            primary_matchpoint=template.primary_matchpoint,
            secondary_matchpoint=template.secondary_matchpoint,
            tertiary_matchpoint=template.tertiary_matchpoint,
        )


class PersistentTemplateFactory(
    GenericFactory[
        Union[
            model.Template,
            schemas.TemplateModel,
            model.PersistentTemplate,
            schemas.PersistentTemplateModel,
        ],
        model.PersistentTemplate,
        schemas.PersistentTemplateModel,
    ]
):
    def to_domain(
        self,
        template: Union[
            model.PersistentTemplate,
            model.Template,
            schemas.PersistentTemplateModel,
            schemas.TemplateModel,
        ],
        id: Optional[Union[int, str]] = None,
        name: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> model.PersistentTemplate:
        id = template.id if hasattr(template, "id") else id
        name = template.name if hasattr(template, "name") else name
        agent = template.agent if hasattr(template, "agent") else agent
        if not id or not name or not agent:
            raise TypeError
        return model.PersistentTemplate(
            id=id,
            name=name,
            agent=agent,
            audience=template.audience,
            blanket_po=template.blanket_po,
            copies=template.copies,
            country=template.country,
            create_date=template.create_date,
            format=template.format,
            fund=template.fund,
            internal_note=template.internal_note,
            lang=template.lang,
            order_type=template.order_type,
            price=template.price,
            selector=template.selector,
            selector_note=template.selector_note,
            source=template.source,
            status=template.status,
            var_field_isbn=template.var_field_isbn,
            vendor_code=template.vendor_code,
            vendor_notes=template.vendor_notes,
            vendor_title_no=template.vendor_title_no,
            primary_matchpoint=template.primary_matchpoint,
            secondary_matchpoint=template.secondary_matchpoint,
            tertiary_matchpoint=template.tertiary_matchpoint,
        )

    def to_pydantic(
        self,
        template: Union[
            model.PersistentTemplate,
            model.Template,
            schemas.PersistentTemplateModel,
            schemas.TemplateModel,
        ],
        id: Optional[Union[int, str]] = None,
        name: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> schemas.PersistentTemplateModel:
        id = template.id if hasattr(template, "id") else id
        name = template.name if hasattr(template, "name") else name
        agent = template.agent if hasattr(template, "agent") else agent
        if not id or not name or not agent:
            raise TypeError
        return schemas.PersistentTemplateModel(
            id=id,
            name=name,
            agent=agent,
            audience=template.audience,
            blanket_po=template.blanket_po,
            copies=template.copies,
            country=template.country,
            create_date=template.create_date,
            format=template.format,
            fund=template.fund,
            internal_note=template.internal_note,
            lang=template.lang,
            order_type=template.order_type,
            price=template.price,
            selector=template.selector,
            selector_note=template.selector_note,
            source=template.source,
            status=template.status,
            var_field_isbn=template.var_field_isbn,
            vendor_code=template.vendor_code,
            vendor_notes=template.vendor_notes,
            vendor_title_no=template.vendor_title_no,
            primary_matchpoint=template.primary_matchpoint,
            secondary_matchpoint=template.secondary_matchpoint,
            tertiary_matchpoint=template.tertiary_matchpoint,
        )
