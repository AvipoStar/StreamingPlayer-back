from fastapi import APIRouter, Depends, UploadFile

from config.get_user_from_token import get_user_id_from_token
from controllers.album import addAlbum, removeAlbum, updateAlbum, getAlbumTracks
from models.album import CreateAlbum, Album

router = APIRouter()


@router.post('/', tags=["Album"])
async def add_album(album: CreateAlbum, user_id: int = Depends(get_user_id_from_token)):
    album = await addAlbum(album, user_id)
    return album


@router.delete('/', tags=["Album"])
async def remove_album(album_id: int):
    album = await removeAlbum(album_id)
    return album


@router.put('/', tags=["Album"])
async def update_album(album: Album, preview: UploadFile):
    album = await updateAlbum(album, preview)
    return album


@router.get('/{album_id}', tags=["Album"])
async def get_album_tracks(album_id: int, user_id: int = Depends(get_user_id_from_token)):
    album = await getAlbumTracks(album_id, user_id)
    return album
