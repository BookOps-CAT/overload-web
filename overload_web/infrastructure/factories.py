from overload_web.domain.logic import bib_matcher
from overload_web.infrastructure.bibs import marc_adapters, sierra


def get_matcher_for_library(library: str, matchpoints: list) -> bib_matcher.BibMatcher:
    session: sierra.SierraSessionProtocol
    if library == "bpl":
        session = sierra.BPLSolrSession()
    elif library == "nypl":
        session = sierra.NYPLPlatformSession()
    else:
        raise ValueError("Invalid library. Must be 'bpl' or 'nypl'")
    fetcher = sierra.SierraBibFetcher(session=session, library=library)
    return bib_matcher.BibMatcher(fetcher=fetcher, matchpoints=matchpoints)


def get_parser_for_library(library: str) -> marc_adapters.BookopsMarcTransformer:
    return marc_adapters.BookopsMarcTransformer(library=library)
