from fastapi import FastAPI

from overload_web import services
from overload_web.domain import model
from overload_web.entry_points import config

app = FastAPI()


@app.get("/")
def root(application: str = "Overload Web"):
    return {"application": application}


@app.get("/about")
def about(application: str = "Overload Web"):
    return {"application": application}


@app.post("/attach")
def attach_endpoint(bib_id: str, order: model.Order):
    bib = services.attach(order_data=order, matched_bib_id=bib_id)
    return {"bib": bib}


@app.post("/vendor_file")
def process_vendor_file(
    library: str, order: model.Order, template: model.OrderTemplate
):
    session_adapter = config.get_session_adapter(library=library)
    processed_bib = services.process_file(
        sierra_service=session_adapter, order_data=order, template=template
    )
    return {"bib": processed_bib}
