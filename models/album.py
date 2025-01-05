from typing import Optional

from pydantic import BaseModel
from datetime import date


class Album(BaseModel):
    id: Optional[int]
    title: str
    release_date: date
    preview_url: str


class CreateAlbum(BaseModel):
    title: str
    preview_url: str
    release_date: date

