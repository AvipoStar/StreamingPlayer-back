from fastapi import APIRouter, Depends

from config.get_user_from_token import get_user_id_from_token
from controllers.author import getTracks, getAlbums, getAuthorInfo

router = APIRouter()


@router.get('/{author_id}', tags=["Author"])
async def get_author(author_id: int):
    authors = await getAuthorInfo(author_id)
    return authors


@router.get('/getTracks/{author_id}', tags=["Author"])
async def get_tracks(author_id: int, user_id: int = Depends(get_user_id_from_token)):
    tracks = await getTracks(author_id, user_id)
    return tracks


@router.get('/getAlbums/{author_id}', tags=["Author"])
async def get_albums(author_id: int):
    albums = await getAlbums(author_id)
    return albums
