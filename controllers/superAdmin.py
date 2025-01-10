from http.client import HTTPException

import aiomysql
from starlette import status

from config.Database import get_connection
from models.superAdmin import UserCreate, UserRoleCreate, UserPrivilegeCreate


async def createUser(user: UserCreate):
    db = await get_connection()
    async with db.cursor() as cursor:
        try:
            query = """
                INSERT INTO users (email, password, name, surname, patronymic, bornDate, nickname, is_author, photo_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
            values = (user.email, user.password, user.name, user.surname, user.patronymic, user.bornDate, user.nickname,
                      user.is_author, user.photo_url)
            await cursor.execute(query, values)
            await db.commit()
            user_id = cursor.lastrowid
            return {"id": user_id, **user.dict()}
        except aiomysql.Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка создания пользователя"
            )
        finally:
            await cursor.close()
            db.close()


async def readUsers():
    db = await get_connection()
    async with db.cursor() as cursor:
        try:
            query = "SELECT * FROM users"
            await cursor.execute(query)
            result = await cursor.fetchall()
            return result
        except aiomysql.Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка получения пользователей"
            )
        finally:
            await cursor.close()
            db.close()


async def readUser(user_id: int):
    db = await get_connection()
    async with db.cursor() as cursor:
        try:
            query = "SELECT * FROM users WHERE id = %s"
            await cursor.execute(query, (user_id,))
            result = await cursor.fetchone()
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Пользователь не найден"
                )
            return result
        except aiomysql.Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка получения пользователя"
            )
        finally:
            await cursor.close()
            db.close()


async def updateUser(user_id: int, user: UserCreate):
    db = await get_connection()
    async with db.cursor() as cursor:
        try:
            query = """
            UPDATE users
            SET email = %s, password = %s, name = %s, surname = %s, patronymic = %s, bornDate = %s, nickname = %s, is_author = %s, photo_url = %s
            WHERE id = %s
            """
            values = (user.email, user.password, user.name, user.surname, user.patronymic, user.bornDate, user.nickname,
                      user.is_author, user.photo_url, user_id)
            await cursor.execute(query, values)
            await db.commit()
            return {"id": user_id, **user.dict()}
        except aiomysql.Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка обновления пользователя"
            )
        finally:
            await cursor.close()
            db.close()


async def deleteUser(user_id: int):
    db = await get_connection()
    async with db.cursor() as cursor:
        try:
            query = "DELETE FROM users WHERE id = %s"
            await cursor.execute(query, (user_id,))
            await db.commit()
            return {"id": user_id, "detail": "Пользователь удален"}
        except aiomysql.Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка удаления пользователя"
            )
        finally:
            await cursor.close()
            db.close()


async def createRole(role: UserRoleCreate):
    db = await get_connection()
    async with db.cursor() as cursor:
        try:
            query = "INSERT INTO user_roles (role_name) VALUES (%s)"
            await cursor.execute(query, (role.role_name,))
            await db.commit()
            role_id = cursor.lastrowid
            return {"id": role_id, "role_name": role.role_name}
        except aiomysql.Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка создания роли"
            )
        finally:
            await cursor.close()
            db.close()


async def createPrivilege(privilege: UserPrivilegeCreate):
    db = await get_connection()
    async with db.cursor() as cursor:
        try:
            query = "INSERT INTO user_privileges (user_id, role_id) VALUES (%s, %s)"
            await cursor.execute(query, (privilege.user_id, privilege.role_id))
            await db.commit()
            return {"user_id": privilege.user_id, "role_id": privilege.role_id}
        except aiomysql.Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка создания привилегии"
            )
        finally:
            await cursor.close()
            db.close()
