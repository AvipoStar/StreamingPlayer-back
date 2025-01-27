from datetime import date

from pydantic import BaseModel


class StringValue(BaseModel):
    value: str


class NumberValue(BaseModel):
    value: int


class DatePeriod(BaseModel):
    dateStart: str
    dateEnd: str
