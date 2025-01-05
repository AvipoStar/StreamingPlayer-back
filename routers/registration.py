from fastapi import APIRouter

from controllers.registration import register_user
from models.registration import Registration

router = APIRouter()


@router.post('/register', tags=["Auth"])
async def auth(registrationData: Registration):
    user = await register_user(registrationData)
    return user
