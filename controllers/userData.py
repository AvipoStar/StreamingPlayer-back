import aiomysql
from fastapi import FastAPI, HTTPException, status
from config.Database import get_connection

app = FastAPI()


async def getUserDetails(user_id: int):
    db = await get_connection()
    async with db.cursor(aiomysql.DictCursor) as cursor:
        try:
            # Запрос к базе данных для получения данных пользователя по user_id с дешифрованием данных
            query = """
                SELECT
                    StreamingPlayer.decrypt_data(u.surname) AS surname,
                    StreamingPlayer.decrypt_data(u.name) AS name,
                    StreamingPlayer.decrypt_data(u.patronymic) AS patronymic,
                    u.bornDate,
                    StreamingPlayer.decrypt_data(u.email) AS email,
                    ur.role_id,
                    u.is_author,
                    u.nickname,
                    u.photo_url
                FROM users u
                JOIN user_roles ur ON ur.user_id = u.id
                WHERE u.id = %s
            """
            await cursor.execute(query, (user_id,))
            result = await cursor.fetchone()

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Пользователь не найден"
                )

            return {
                "userId": user_id,
                "surname": result['surname'],
                "name": result['name'],
                "patronymic": result['patronymic'],
                "bornDate": result['bornDate'],
                "email": result['email'],
                'role_id': result['role_id'],
                'is_author': result['is_author'],
                'nickname': result['nickname'],
                'photo_url': result['photo_url']
            }

        except aiomysql.Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка получения данных пользователя"
            )
        finally:
            await cursor.close()
            db.close()
