from fastapi import FastAPI, HTTPException, status
from config.Database import get_connection
from aiomysql import Error

app = FastAPI()


async def getUserDetails(user_id: int):
    db = await get_connection()
    async with db.cursor() as cursor:
        try:
            # Запрос к базе данных для получения данных пользователя по user_id
            await cursor.execute("""
                SELECT u.surname, u.name, u.patronymic, u.bornDate, u.email, ur.role_id, u.is_author, u.nickname, u.photo_url
                FROM users u
                JOIN user_roles ur ON ur.user_id = u.id
                WHERE u.id = %s
            """, (user_id,))
            result = await cursor.fetchone()

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Пользователь не найден"
                )

            surname, name, patronymic, bornDate, email, role_id, is_author, nickname, photo_url = result

            return {
                "userId": user_id,
                "surname": surname,
                "name": name,
                "patronymic": patronymic,
                "bornDate": bornDate,
                "email": email,
                'role_id': role_id,
                'is_author': is_author,
                'nickname': nickname,
                'photo_url': photo_url
            }

        except Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка получения данных пользователя"
            )
        finally:
            await cursor.close()
            db.close()
