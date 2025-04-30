from typing import Any, Dict, List, Protocol, runtime_checkable


@runtime_checkable
class BibFetcher(Protocol):
    def get_bibs_by_id(self, value: str | int, key: str) -> List[Dict[str, Any]]: ...
