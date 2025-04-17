from typing import Annotated, Optional, Sequence

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse

from overload_web.application import services, unit_of_work
from overload_web.presentation.api import schemas

api_router = APIRouter()


@api_router.get("/")
def root() -> JSONResponse:
    return JSONResponse(content={"app": "Overload Web"})


@api_router.post("/vendor_file")
def vendor_file_process(
    file: Annotated[UploadFile, File(...)],
    library: Annotated[str, Form()],
    destination: Annotated[Optional[str], Form()] = None,
    template: schemas.TemplateModel = Depends(schemas.TemplateModel.from_form_data),
) -> Sequence[schemas.BibModel]:
    processed_bibs = []
    uow = unit_of_work.OverloadUnitOfWork(library=library)
    bibs = services.process_marc_file(bib_data=file.file, library=library, uow=uow)
    model_template = uow.template_factory.to_domain(template=template)
    for bib in bibs:
        for order in bib.orders:
            order.apply_template(template=model_template)
        matchpoints = model_template.matchpoints
        processed_bibs.append(
            services.match_bib(bib=bib.__dict__, matchpoints=matchpoints, uow=uow)
        )
    return [schemas.BibModel(**i) for i in processed_bibs]
