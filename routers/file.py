from fastapi import APIRouter, File, UploadFile

from controllers.file import uploadFile

router = APIRouter()


@router.post("/", tags=["Files"])
async def upload_file(file: UploadFile = File(...)):
    result = await uploadFile(file)
    return result
