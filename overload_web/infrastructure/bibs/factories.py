from overload_web.domain import logic, models
from overload_web.infrastructure.bibs import marc, sierra


def get_matcher_for_library(library: str, matchpoints: list) -> logic.bibs.BibMatcher:
    session: sierra.SierraSessionProtocol
    if library == "bpl":
        session = sierra.BPLSolrSession()
    elif library == "nypl":
        session = sierra.NYPLPlatformSession()
    else:
        raise ValueError("Invalid library. Must be 'bpl' or 'nypl'")
    fetcher = sierra.SierraBibFetcher(session=session, library=library)
    return logic.bibs.BibMatcher(fetcher=fetcher, matchpoints=matchpoints)


def get_parser_for_library(library: str) -> marc.BookopsMarcTransformer:
    if library not in ["bpl", "nypl"]:
        raise ValueError("Invalid library. Must be 'bpl' or 'nypl'")
    return marc.BookopsMarcTransformer(library=models.bibs.LibrarySystem(library))
