from typing import Optional, List

from fastapi import File
from pydantic import BaseModel
from datetime import datetime


class MediaItem(BaseModel):
    id: Optional[int]
    title: str
    description: str
    cover_url: str
    category_id: int
    release_date: datetime
    duration: int
    album_id: int
    genre_ids: List[int]
    file_size: int
    content_type: str
    file_url: str


class CreateMediaItem(BaseModel):
    title: str
    description: str
    album_id: int
    genre_ids: List[int]
    file_path: str
    preview_path: Optional[str]
