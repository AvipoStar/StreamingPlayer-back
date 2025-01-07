import time
from http.client import HTTPException

import aiofiles
from starlette import status

from config.Database import get_connection
from config.create_access_token import createAccessToken
from config.hash_password import hash_password
from models.registration import Registration


async def register_user(user: Registration):
    start_time = time.time()  # Замеряем время начала выполнения

    db = await get_connection()
    async with db.cursor() as cursor:
        try:
            # Хэширование пароля
            hashed_password = await hash_password(user.password)

            # Вставка нового пользователя в базу данных с шифрованием данных
            query = """
            INSERT INTO users (email, password, surname, name, patronymic, bornDate)
            VALUES (
                encrypt_data(%s), 
                %s, 
                encrypt_data(%s), 
                encrypt_data(%s), 
                encrypt_data(%s), 
                %s
            )
            """
            values = (user.email, hashed_password, user.surname, user.name, user.patronymic, user.bornDate)
            await cursor.execute(query, values)
            await db.commit()

            # Получение ID нового пользователя
            user_id = cursor.lastrowid

            await cursor.execute("INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)", (user_id, 1))
            await db.commit()

            # Создание токена
            access_token = createAccessToken(user.email, user_id)

            return {
                "user_id": user_id,
                "access_token": access_token
            }

        except Exception as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка регистрации пользователя"
            )
        finally:
            await cursor.close()
            db.close()
