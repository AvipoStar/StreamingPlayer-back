from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TrackUser(BaseModel):
    track_id: int
    user_id: int
