from typing import Dict

from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/")
def root() -> Dict[str, str]:
    return {"app": "Overload Web"}
