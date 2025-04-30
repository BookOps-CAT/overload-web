from typing import Annotated, Optional, Sequence

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse

from overload_web.application import services
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
    form_data: schemas.TemplateModel = Depends(schemas.TemplateModel.from_form_data),
) -> Sequence[schemas.BibModel]:
    template_data = {k: v for k, v in form_data.__dict__.items() if k != "matchpoints"}
    processed_bibs = services.match_and_attach(
        file_data=file.file,
        library=library,
        matchpoints=form_data.matchpoints.as_list(),
        template=template_data,
    )
    return [schemas.BibModel(**i) for i in processed_bibs]
