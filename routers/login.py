import time

from fastapi import APIRouter

from controllers.login import login, loginToken
from models.login import LoginClass
from models.token import Token

router = APIRouter()


@router.post('/login', tags=["Auth"])
async def auth(loginData: LoginClass):
    user = await login(loginData.email, loginData.password)
    return user


@router.post('/loginToken', tags=["Auth"])
async def auth_token(token: Token):
    user_id = await loginToken(token.value)
    return user_id
