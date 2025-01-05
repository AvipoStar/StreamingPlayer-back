from fastapi import APIRouter, Depends

from config.get_user_from_token import get_user_id_from_token
from controllers.userSettings import editUserProfile, resetPasswordRequest, resetPasswordResponse, \
    getResetPasswordRequests, becomeAuthor
from models.simpleValues import StringValue
from models.userSettings import EditUser, ResetPasswordRequest, ResetPasswordResponse

router = APIRouter()


@router.put('/editUserProfile', tags=["UserSettings"])
async def change_user_settings(userData: EditUser, user_id: int = Depends(get_user_id_from_token)):
    result = await editUserProfile(userData, user_id)
    return result


@router.post('/resetPasswordRequest', tags=["UserSettings"])
async def reset_password_request(data: ResetPasswordRequest):
    result = await resetPasswordRequest(data.mail, data.new_password)
    return result


@router.post('/resetPasswordResponse', tags=["UserSettings"])
async def reset_password_response(request_id: ResetPasswordResponse):
    result = await resetPasswordResponse(request_id.id)
    return result


@router.get('/resetPasswordRequests', tags=["UserSettings"])
async def get_reset_password_response():
    result = await getResetPasswordRequests()
    return result


@router.put('/becomeAuthor', tags=["UserSettings"])
async def become_author(nickname: StringValue, user_id: int = Depends(get_user_id_from_token)):
    result = await becomeAuthor(user_id, nickname.value)
    return result
