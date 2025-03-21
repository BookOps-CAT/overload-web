from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends, File, UploadFile

from overload_web import config
from overload_web.adapters import schemas
from overload_web.domain import model
from overload_web.services import handlers

api_router = APIRouter()


@api_router.get("/")
def root() -> Dict[str, str]:
    return {"app": "Overload Web"}


@api_router.post("/vendor_file")
def vendor_file_process(
    file: Annotated[UploadFile, File(...)],
    form_data: Annotated[Any, Depends(schemas.get_form_data)],
) -> Dict[str, Any]:
    library, destination, template = form_data
    processed_bibs = []
    order_bibs = schemas.read_marc_file(marc_file=file, library=library)
    for bib in order_bibs:
        processed_bibs.append(
            handlers.process_file(
                sierra_service=config.get_sierra_service(library=library),
                order_bib=model.OrderBib(
                    bib_id=bib.bib_id, orders=bib.orders, library=library
                ),
                template=model.OrderTemplate(**template.model_dump()),
            )
        )
    return {
        "template": template,
        "processed_bibs": processed_bibs,
    }
