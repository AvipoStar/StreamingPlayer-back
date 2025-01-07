import os

import aiomysql
import openpyxl as openpyxl
import pandas as pd
from starlette import status
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse

from config.Database import get_connection


async def get_table_row_counts():
    db = await get_connection()
    async with db.cursor() as cursor:
        try:
            await cursor.execute("SHOW TABLES")
            tables = await cursor.fetchall()

            results = []

            for table in tables:
                await cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                row_count = await cursor.fetchone()
                results.append({"tableName": table[0], "rowCount": row_count[0]})

            return results
        except aiomysql.Error as e:
            print(f"Database error: {e}")
            raise
        finally:
            if cursor:
                await cursor.close()
            if db:
                db.close()


async def export_author_to_file(user_id: int):
    temp_dir = "/temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    file_path = os.path.join(temp_dir, "author_data.csv")

    # Проверка наличия файла и его создание, если он не существует
    if not os.path.exists(file_path):
        print('\n------------------------------\n Файл не существует\n------------------------------\n ')
        open(file_path, 'w').close()

    if os.path.exists(file_path):
        print('\n------------------------------\n Файл существует\n------------------------------\n ')

    db = await get_connection()
    async with db.cursor() as cursor:
        try:
            # Запрос данных автора
            query_user = """
            SELECT
                StreamingPlayer.decrypt_data(u.surname) AS surname,
                StreamingPlayer.decrypt_data(u.name) AS name,
                StreamingPlayer.decrypt_data(u.patronymic) AS patronymic,
                u.bornDate,
                StreamingPlayer.decrypt_data(u.email) AS email,
                ur.role_id,
                u.is_author,
                u.nickname
            FROM users u
            JOIN user_roles ur ON ur.user_id = u.id
            WHERE u.id = %s
            """
            await cursor.execute(query_user, (user_id,))
            user_data = await cursor.fetchone()

            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Данные автора не найдены"
                )

            # Запрос данных альбомов автора
            query_albums = """
            SELECT a1.id, a1.title
            FROM users u
            JOIN authors a ON u.id = a.user_id
            JOIN albums a1 ON a.album_id = a1.id
            WHERE u.id = %s
            """
            await cursor.execute(query_albums, (user_id,))
            albums_data = await cursor.fetchall()

            # Запрос данных треков автора
            query_tracks = """
            SELECT mi.id, mi.title, mi.duration
            FROM media_items mi
            JOIN albums a ON mi.album_id = a.id
            JOIN authors a1 ON a.id = a1.album_id
            JOIN users u ON a1.user_id = u.id
            WHERE a1.user_id = %s
            """
            await cursor.execute(query_tracks, (user_id,))
            tracks_data = await cursor.fetchall()
            # Создание DataFrame для данных автора
            user_headers = [
                "Surname", "Name", "Patronymic", "Born Date", "Email", "Role ID", "Is Author", "Nickname"
            ]
            user_df = pd.DataFrame([user_data], columns=user_headers)

            # Создание DataFrame для данных альбомов
            albums_headers = ["Album ID", "Album Title"]
            albums_df = pd.DataFrame(albums_data, columns=albums_headers)

            # Создание DataFrame для данных треков
            tracks_headers = ["Track ID", "Track Title", "Track Duration"]
            tracks_df = pd.DataFrame(tracks_data, columns=tracks_headers)

            # Сохранение данных в CSV-файл
            with open(file_path, 'w', newline='') as f:
                user_df.to_csv(f, index=False)
                f.write("\n")
                albums_df.to_csv(f, index=False)
                f.write("\n")
                tracks_df.to_csv(f, index=False)

            # Возвращение файла в ответе
            return FileResponse(file_path, filename="author_data.csv", media_type='text/csv')

        except aiomysql.Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка получения данных"
            )
        finally:
            await cursor.close()
            db.close()
            # Удаление файла после отправки
            if os.path.exists(file_path):
                os.remove(file_path)
