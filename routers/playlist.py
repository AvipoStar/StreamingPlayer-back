from fastapi import APIRouter, Depends

from config.get_user_from_token import get_user_id_from_token
from controllers.playlist import createPlaylist, deletePlaylist, changeName, getUserPlaylists, \
    getPlaylistTracks, toggleTrack
from models.playlist import Playlist, TrackPlaylist, CreatePlaylist
from models.simpleValues import StringValue

router = APIRouter()


@router.post('/', tags=["Playlist"])
async def create_playlist_endpoint(playlist: StringValue, user_id: int = Depends(get_user_id_from_token)):
    playlist_id = await createPlaylist(playlist.value, user_id)
    return {"playlist_id": playlist_id}


@router.delete('/', tags=["Playlist"])
async def delete_playlist_endpoint(playlist_id: int):
    result = await deletePlaylist(playlist_id)
    return result


@router.put('/', tags=["Playlist"])
async def update_playlist_endpoint(playlist: createPlaylist):
    result = await changeName(playlist)
    return result


@router.post("/toggleTrack", tags=["Playlist"])
async def toggle_playlist_track(data: TrackPlaylist):
    result = await toggleTrack(data.track_id, data.playlist_id)
    return result


@router.get('/', tags=["Playlist"])
async def get_playlists_endpoint(user_id: int = Depends(get_user_id_from_token)):
    result = await getUserPlaylists(user_id)
    return result


@router.get('/{playlist_id}', tags=["Playlist"])
async def get_playlists_endpoint(playlist_id: int, user_id: int = Depends(get_user_id_from_token)):
    result = await getPlaylistTracks(playlist_id, user_id)
    return result
