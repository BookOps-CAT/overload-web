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
    bibs = services.process_marc_file(bib_data=file.file, library=library)
    for bib in bibs:
        for order in bib.orders:
            order.apply_template(template_data=vars(template))
        processed_bibs.append(
            services.match_bib(
                bib=bib.__dict__,
                matchpoints=template.matchpoints.as_list(),
                uow=uow,
            )
        )
    return [schemas.BibModel(**i) for i in processed_bibs]
