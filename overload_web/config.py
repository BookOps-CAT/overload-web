import json
import os
from functools import lru_cache

from fastapi.templating import Jinja2Templates


def get_postgres_uri() -> str:
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", 5432)
    password = os.environ.get("POSTGRES_PASSWORD", "")
    user = os.environ.get("POSTGRES_USER", "overload")
    db_name = os.environ.get("POSTGRES_DB", "overload_dev")
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


@lru_cache
def get_templates() -> Jinja2Templates:
    with open("overload_web/form_constants.json", "r", encoding="utf-8") as fh:
        constants = json.load(fh)
    templates = Jinja2Templates(directory="overload_web/presentation/templates")
    templates.env.globals["fixed_fields"] = constants["fixed_fields"]
    templates.env.globals["var_fields"] = constants["var_fields"]
    templates.env.globals["matchpoints"] = constants["matchpoints"]
    templates.env.globals["bib_formats"] = constants["material_form"]
    templates.env.globals["context_fields"] = constants["context_fields"]
    templates.env.globals["vendors"] = constants["vendors"]
    templates.env.globals["application"] = "Overload Web"
    return templates
