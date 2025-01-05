from fastapi import APIRouter, File, UploadFile, HTTPException
import os
import hashlib
from PIL import Image
from io import BytesIO

router = APIRouter()


def calculate_file_hash(file_content):
    hash_object = hashlib.md5()
    hash_object.update(file_content)
    return hash_object.hexdigest()


async def uploadFile(file: UploadFile = File(...)):
    file_content = await file.read()
    file_hash = calculate_file_hash(file_content)
    file_extension = os.path.splitext(file.filename)[1]
    file_path = os.path.join('/var/www/uploads/', f"{file_hash}{file_extension}")

    # Проверяем существует ли файл с таким хэшем
    if not os.path.exists(file_path):
        if file.content_type.startswith('image/'):
            # Если файл является изображением, сжимаем его
            try:
                image = Image.open(BytesIO(file_content))
                image = image.convert("RGB")  # Преобразуем изображение в формат RGB
                image_bytes = BytesIO()
                image.save(image_bytes, format='JPEG',
                           quality=85)  # Сохраняем изображение в формате JPEG с качеством 85%
                file_content = image_bytes.getvalue()
                file_extension = '.jpg'
                file_path = os.path.join('/var/www/uploads/', f"{file_hash}{file_extension}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ошибка при обработке изображения: {str(e)}")

        with open(file_path, "wb") as f:
            f.write(file_content)
        return {"filePath": file_path}
    else:
        return {"filePath": file_path}
