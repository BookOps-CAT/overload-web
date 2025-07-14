import json


def get_context_form_fields() -> dict[str, dict[str, str | dict[str, str]]]:
    with open("overload_web/presentation/templates/context.json", "r") as fh:
        form_fields = json.load(fh)
    return form_fields
