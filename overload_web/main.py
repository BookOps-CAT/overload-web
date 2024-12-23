from typing import List
from fastapi import FastAPI

from overload_web import services, config
from overload_web.domain import model


app = FastAPI()


@app.get("/")
def root(application: str = "Overload Web"):
    return {"application": application}


@app.get("/about")
def about(application: str = "Overload Web"):
    return {"application": application}


@app.post("/attach")
def attach_endpoint(order: model.Order, bib_ids: List[str]):
    bib = services.attach(order_data=order, bib_ids=bib_ids)
    return {"bib": bib}


@app.post("/vendor_file")
def process_vendor_file(
    library: str, order: model.Order, template: model.OrderTemplate
):
    processed_bib = services.process_file(
        sierra_service=config.get_sierra_service(library=library),
        order_data=order,
        template=template,
    )
    return {"bib": processed_bib}
