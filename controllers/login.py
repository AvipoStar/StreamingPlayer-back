import time

import jwt
from fastapi import FastAPI, HTTPException, status

from config.Database import get_connection
from config.create_access_token import createAccessToken, decodeAccessToken
from config.hash_password import hash_password

app = FastAPI()


async def login(email: str, password: str):
    db = await get_connection()
    async with db.cursor() as cursor:
        try:
            await cursor.execute("SELECT id, password, surname, name FROM users WHERE email = encrypt_data(%s)",
                                 (email,))
            result = await cursor.fetchone()

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Пользователь не найден"
                )

            user_id, db_password, encrypted_surname, encrypted_name = result

            hashed_password = await hash_password(password)

            if db_password != hashed_password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверный пароль"
                )

        finally:
            await cursor.close()
            db.close()

    access_token = createAccessToken(email, user_id)

    return {
        "user_id": user_id,
        "access_token": access_token
    }


async def loginToken(token: str):
    try:
        # Декодирование токена
        payload = decodeAccessToken(token)
        user_id = payload.get("user_id")

        print('user_id', user_id)

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный токен"
            )

        # Если токен действителен, возвращаем подтверждение
        return {"message": "Токен действителен", "user_id": user_id}

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Срок действия токена истек"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен"
        )
