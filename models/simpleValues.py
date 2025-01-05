from pydantic import BaseModel


class StringValue(BaseModel):
    value: str


class NumberValue(BaseModel):
    value: int
