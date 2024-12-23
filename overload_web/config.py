import os
from overload_web import sierra_adapters


def get_sierra_service(library: str) -> sierra_adapters.SierraService:
    adapter: sierra_adapters.AbstractSierraSession
    if library == "bpl":
        adapter = sierra_adapters.BPLSolrSession()
    elif library == "nypl":
        adapter = sierra_adapters.NYPLPlatformSession()
    else:
        raise ValueError("Invalid library. Must be 'bpl' or 'nypl'")
    return sierra_adapters.SierraService(adapter)


def get_api_url() -> str:
    host = os.environ.get("API_HOST", "localhost")
    port = 8501 if host == "localhost" else 80
    return f"https://{host}:{port}"


def get_current_state():
    """
    Configure system based on the library chosen in a form
    """
    library = os.environ.get("CURRENT_LIBRARY", None)
    return library
