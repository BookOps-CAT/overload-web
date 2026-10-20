import html


def safe_html(template: str, **kwargs) -> str:
    """Escapes all kwargs and formats them into the template string."""
    escaped_kwargs = {key: html.escape(str(value)) for key, value in kwargs.items()}
    return template.format(**escaped_kwargs)
