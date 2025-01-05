from pydantic import BaseModel


class Token(BaseModel):
    value: str
