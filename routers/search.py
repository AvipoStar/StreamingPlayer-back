
from fastapi import APIRouter

from controllers.search import search_media

router = APIRouter()


@router.get("/{search}", tags=["Search"])
async def Search(search: str):
    result = await search_media(search)
    return result

