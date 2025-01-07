from fastapi import FastAPI, HTTPException, status
from config.Database import get_connection
from mysql.connector import Error

from config.hash_password import hash_password
from models.userSettings import EditUser

app = FastAPI()


async def editUserProfile(user: EditUser, user_id: int):
    print('\nuser', user)
    db = await get_connection()
    async with db.cursor() as cursor:
        new_password_hash = await hash_password(user.password)
        try:
            query = """
            UPDATE users
            SET
                email = StreamingPlayer.encrypt_data(%s),
                password = %s,
                name = StreamingPlayer.encrypt_data(%s),
                surname = StreamingPlayer.encrypt_data(%s),
                patronymic = StreamingPlayer.encrypt_data(%s),
                bornDate = %s,
                photo_url = %s
            WHERE id = %s
            """
            values = (
                user.email, new_password_hash, user.name, user.surname, user.patronymic, user.bornDate,
                user.photo_url, user_id
            )
            await cursor.execute(query, values)
            await db.commit()

            return user_id

        except Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка обновления пользователя"
            )
        finally:
            await cursor.close()
            db.close()


async def resetPasswordRequest(user_mail: str, new_password: str):
    db = await get_connection()
    async with db.cursor() as cursor:
        try:
            await cursor.execute("SELECT id FROM users WHERE email = StreamingPlayer.encrypt_data(%s)", (user_mail,))
            user_id = await cursor.fetchone()
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Mail не найден"
                )
            user_id = user_id[0]

            await cursor.execute("SELECT * FROM password_reset_requests WHERE user_id = %s", (user_id,))
            result = await cursor.fetchone()
            if result:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Запрос на сброс пароля уже существует"
                )
            else:
                await cursor.execute("INSERT INTO password_reset_requests (user_id, new_password) VALUES (%s, %s)",
                                     (user_id, new_password))
                await db.commit()
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
                return True
        except Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка запроса на сброс пароля"
            )
        finally:
            await cursor.close()
            db.close()


async def resetPasswordResponse(request_id: int):
    db = await get_connection()
    async with db.cursor() as cursor:
        try:
            await cursor.execute("SELECT user_id, new_password FROM password_reset_requests WHERE id = %s",
                                 (request_id,))
            result = await cursor.fetchone()
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Не найден запрос на сброс пароля"
                )
            user_id, new_password = result

            new_password_hash = await hash_password(new_password)

            await cursor.execute("UPDATE users SET password = %s WHERE id = %s", (new_password_hash, user_id))
            await cursor.execute("DELETE FROM password_reset_requests WHERE id = %s", (request_id,))
            await db.commit()

        except Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка сброса пароля"
            )
        finally:
            await cursor.close()
            db.close()


async def getResetPasswordRequests():
    db = await get_connection()
    async with db.cursor() as cursor:
        try:
            await cursor.execute("""SELECT prr.id, StreamingPlayer.decrypt_data(u.email) AS email
                                    FROM password_reset_requests prr
                                    JOIN users u ON u.id = prr.user_id;""")
            result = await cursor.fetchall()

            if len(result) == 0:
                return []

            requests = []

            for req in result:
                req_id, user_mail = req
                requests.append({"id": req_id, "mail": user_mail})

            return requests

        except Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка получения запросов"
            )
        finally:
            await cursor.close()
            db.close()


async def becomeAuthor(user_id: int, nickname: str):
    db = await get_connection()
    async with db.cursor() as cursor:
        try:
            await cursor.execute("UPDATE users SET nickname = %s, is_author = %s WHERE id = %s ",
                                 (nickname, 1, user_id))
            await db.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Playlist not found")
            else:
                return True

        except Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка получения запросов"
            )
        finally:
            await cursor.close()
            db.close()
