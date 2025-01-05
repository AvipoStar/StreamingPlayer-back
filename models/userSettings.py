from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    id: int
    email: str
    password: str
    name: str
    surname: str
    patronymic: str
    bornDate: datetime
    nickname: str
    created_at: datetime
    photo_url: str = None


class EditUser(BaseModel):
    email: str
    password: str
    name: str
    surname: str
    patronymic: str
    bornDate: datetime
    photo_url: str = None


class ResetPasswordRequest(BaseModel):
    mail: str
    new_password: str


class ResetPasswordResponse(BaseModel):
    id: int
