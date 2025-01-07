from fastapi import APIRouter, Depends

from config.get_user_from_token import get_user_id_from_token
from controllers.genre import getGenres, getGenreTracks

router = APIRouter()


@router.get('/', tags=["Genre"])
async def get_genres():
    result = await getGenres()
    return result


@router.get('/{genre_id}', tags=["Genre"])
async def get_genres(genre_id: int, user_id: int = Depends(get_user_id_from_token)):
    result = await getGenreTracks(genre_id, user_id)
    return result
