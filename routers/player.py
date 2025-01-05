from fastapi import APIRouter

from controllers.player import stream_music, track_list

router = APIRouter()


@router.get("/audio/{file_id}", tags=["Player"])
async def stream_audio(file_id: int):
    streaming_response = await stream_music(file_id)
    return streaming_response


@router.get("/tracks", tags=["Player"])
async def list_tracks():
    tracks = await track_list()
    return tracks
