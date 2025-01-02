from overload_web.adapters import sierra_adapters


def get_sierra_service(library: str) -> sierra_adapters.SierraService:
    adapter: sierra_adapters.AbstractSierraSession
    if library == "bpl":
        adapter = sierra_adapters.BPLSolrSession()
    elif library == "nypl":
        adapter = sierra_adapters.NYPLPlatformSession()
    else:
        raise ValueError("Invalid library. Must be 'bpl' or 'nypl'")
    return sierra_adapters.SierraService(adapter)
