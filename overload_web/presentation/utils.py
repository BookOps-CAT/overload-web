"""Utility functions used by presentation layer."""

import html
from typing import Any


def safe_html(template: str, **kwargs: Any) -> str:
    """Escapes all kwargs and formats them into the template string."""
    escaped_kwargs = {key: html.escape(str(value)) for key, value in kwargs.items()}
    return template.format(**escaped_kwargs)
