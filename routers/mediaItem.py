from fastapi import APIRouter, UploadFile, Depends

from config.get_user_from_token import get_user_id_from_token
from controllers.mediaItem import addMediaItem, updateMediaItem, removeMediaItem, getMediaItems, miInPlaylists, \
    getMediaItemDetails, get_latest_tracks, get_listening_history
from models.mediaItem import CreateMediaItem, MediaItem

router = APIRouter()


@router.post('/', tags=["MediaItem"])
async def add_media_item(item: CreateMediaItem, user_id: int = Depends(get_user_id_from_token)):
    media_item_id = await addMediaItem(item, user_id)
    return media_item_id


@router.delete('/', tags=["MediaItem"])
async def remove_media_item(item_id: int):
    result = await removeMediaItem(item_id)
    return result


@router.put('/', tags=["MediaItem"])
async def update_media_item(item: MediaItem, file: UploadFile, preview: UploadFile):
    result = await updateMediaItem(item, file, preview)
    return result


@router.get('/', tags=["MediaItem"])
async def get_media_items(user_id: int = Depends(get_user_id_from_token)):
    tracks = await getMediaItems(user_id)
    return tracks


@router.get('/containsInPlaylists/{track_id}', tags=["MediaItem"])
async def mi_in_playlists(track_id: int, user_id: int = Depends(get_user_id_from_token)):
    playlists = await miInPlaylists(track_id, user_id)
    return playlists


@router.get('/details/{track_id}', tags=["MediaItem"])
async def track_details(track_id: int):
    track = await getMediaItemDetails(track_id)
    return track


@router.get('/last_tracks', tags=["MediaItem"])
async def last_tracks(user_id: int = Depends(get_user_id_from_token)):
    track = await get_latest_tracks(user_id)
    return track


@router.get('/listening_history', tags=["MediaItem"])
async def listening_history(user_id: int = Depends(get_user_id_from_token)):
    track = await get_listening_history(user_id)
    return track
