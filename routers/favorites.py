from fastapi import APIRouter, Depends

from config.get_user_from_token import get_user_id_from_token
from controllers.favorites import getTracks, toggleTrack, getTracksHTML
from models.simpleValues import NumberValue

router = APIRouter()


@router.post('/', tags=["Favorites"])
async def toggle_track(track_id: NumberValue, user_id: int = Depends(get_user_id_from_token)):
    result = await toggleTrack(track_id.value, user_id)
    return result


@router.get('/', tags=["Favorites"])
async def get_favorites(user_id: int = Depends(get_user_id_from_token)):
    result = await getTracks(user_id)
    return result

@router.get('/getTracksHTML', tags=["Favorites"])
async def get_favorites_html(user_id: int = Depends(get_user_id_from_token)):
    result = await getTracksHTML(user_id)
    return result
