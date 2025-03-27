from typing import Annotated, Optional, Sequence

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse

from overload_web import config
from overload_web.adapters import object_factories
from overload_web.api import schemas
from overload_web.services import handlers

api_router = APIRouter()

bib_factory = object_factories.OrderBibFactory()
template_factory = object_factories.TemplateFactory()


@api_router.get("/")
def root() -> JSONResponse:
    return JSONResponse(content={"app": "Overload Web"})


@api_router.post("/vendor_file")
def vendor_file_process(
    file: Annotated[UploadFile, File(...)],
    library: Annotated[str, Form()],
    destination: Annotated[Optional[str], Form()] = None,
    template: schemas.TemplateModel = Depends(schemas.TemplateModel.from_form_data),
) -> Sequence[schemas.OrderBibModel]:
    processed_bibs = []

    order_bibs = bib_factory.binary_to_domain_list(bib_data=file.file, library=library)
    model_template = template_factory.to_domain(template=template)
    service = config.get_sierra_service(library=library)

    for bib in order_bibs:
        processed_bibs.append(
            handlers.process_file(
                sierra_service=service, order_bib=bib, template=model_template
            )
        )
    return [bib_factory.to_pydantic(i) for i in processed_bibs]
