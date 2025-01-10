from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    surname: str
    patronymic: str
    bornDate: str
    nickname: str
    is_author: int
    photo_url: str


class UserRoleCreate(BaseModel):
    role_name: str


class UserPrivilegeCreate(BaseModel):
    user_id: int
    role_id: int
