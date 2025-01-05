from fastapi import APIRouter
from controllers.genre import getGenres

router = APIRouter()


@router.get('/', tags=["Genre"])
async def get_genres():
    result = await getGenres()
    return result
