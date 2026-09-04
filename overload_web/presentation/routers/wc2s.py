"""API router for Overload Web Worldcat2Sierra."""

from __future__ import annotations

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)


api_router = APIRouter()


@api_router.post("/match_record", response_class=HTMLResponse)
def match_record(
    request: Request,
    file: Annotated[UploadFile, File()],
    id_type: Literal["isbn", "issn", "lccn", "upc", "oclc_number"] = Form(...),
    library: Literal["nypl", "bpl"] = Form(...),
    collection: Literal["BL", "RL", ""] | None = Form(None),
    material_type: Literal["any", "bluray", "dvd", "large_print", "print"] = Form(...),
    action: Literal["catalog", "upgrade"] = Form(...),
    record_level: Literal["1", "2", "3"] = Form(...),
    cat_agency: Literal["DLC", "any"] | None = Form(default=None),
    cat_rules: Literal["RDA", "any"] | None = Form(default=None),
    data_source: Literal["id", "export"] | None = Form(default=None),
) -> HTMLResponse:
    lines = file.file.readlines()
    input_data = [
        {"id": i.decode("utf-8").strip("\r\n"), "id_type": id_type} for i in lines
    ]
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="wc2s_partials/wc2s_results.html",
        context={
            "input_data": input_data,
            "form_data": {
                "library": library,
                "collection": collection,
                "material_type": material_type,
                "action": action,
                "record_level": record_level,
                "required_cataloging_agency": cat_agency,
                "required_cataloging_rules": cat_rules,
                "data_source": data_source,
                "id_type": id_type,
            },
        },
    )
