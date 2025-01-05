from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class createPlaylist(BaseModel):
    name: str
    user_id: int


class Playlist(BaseModel):
    id: Optional[int]
    name: str
    user_id: int
    created_at: Optional[datetime]


class TrackPlaylist(BaseModel):
    track_id: int
    playlist_id: int
