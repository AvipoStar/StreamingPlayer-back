from pydantic import BaseModel


class LoginClass(BaseModel):
    email: str
    password: str
