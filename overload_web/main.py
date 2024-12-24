from typing import List
from fastapi import FastAPI

from overload_web import services, config, schemas
from overload_web.domain import model


app = FastAPI()


@app.get("/")
def root(application: str = "Overload Web", include_in_schema=False):
    return {"application": application}


@app.post("/attach")
def attach_endpoint(order: schemas.OrderModel, bib_ids: List[str]):
    bib = services.attach(order_data=model.Order(**order.model_dump()), bib_ids=bib_ids)
    return {"bib": bib}


@app.post("/vendor_file")
def process_vendor_file(
    order: schemas.OrderModel, template: schemas.OrderTemplateModel
):
    processed_bib = services.process_file(
        sierra_service=config.get_sierra_service(library=order.library),
        order_data=model.Order(**order.model_dump()),
        template=model.OrderTemplate(**template.model_dump()),
    )
    return {"bib": processed_bib}
