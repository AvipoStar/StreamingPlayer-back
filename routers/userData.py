from fastapi import APIRouter, Depends

from config.get_user_from_token import get_user_id_from_token
from controllers.userData import getUserDetails

router = APIRouter()


@router.get('/', tags=["Auth"])
async def get_user_details(user_id: int = Depends(get_user_id_from_token)):
    return await getUserDetails(user_id)
