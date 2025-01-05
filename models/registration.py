from pydantic import BaseModel
from MySQLdb.times import Date

class Registration(BaseModel):
    email: str
    password: str
    surname: str
    name: str
    patronymic: str
    bornDate: Date
