import datetime
import json

import aiomysql
from fastapi import FastAPI, HTTPException, status

from config.Database import get_connection

app = FastAPI()


async def toggleTrack(track_id: int, user_id: int):
    connection = await get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Ошибка подключения к базе данных")

    async with connection.cursor() as cursor:
        try:
            # Проверяем, существует ли запись в таблице favorites
            check_query = "SELECT * FROM favorites WHERE media_item_id = %s AND user_id = %s"
            check_values = (track_id, user_id)
            await cursor.execute(check_query, check_values)
            exists = await cursor.fetchone()

            if exists:
                # Если запись существует, удаляем её
                query = "DELETE FROM favorites WHERE media_item_id = %s AND user_id = %s"
                values = (track_id, user_id)
            else:
                # Если записи нет, добавляем её
                query = "INSERT INTO favorites (media_item_id, user_id, created_at) VALUES (%s, %s, %s)"
                values = (track_id, user_id, datetime.datetime.now())

            await cursor.execute(query, values)
            await connection.commit()
            return True
        except aiomysql.Error as e:
            print(f"Ошибка: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка выполнения действия с треком"
            )
        finally:
            await cursor.close()
            connection.close()


async def getTracks(user_id: int):
    connection = await get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Ошибка подключения к базе данных")

    async with connection.cursor(aiomysql.DictCursor) as cursor:
        query = """
            SELECT
                mi.id,
                mi.title,
                mi.duration,
                a.preview_url,
                au.authors
            FROM favorites f
            JOIN media_items mi ON mi.id = f.media_item_id
            JOIN albums a ON mi.album_id = a.id
            LEFT JOIN (
                SELECT
                    a1.album_id,
                    JSON_ARRAYAGG(
                        JSON_OBJECT('id', a1.user_id, 'nickname', u.nickname)
                    ) AS authors
                FROM authors a1
                JOIN users u ON a1.user_id = u.id
                GROUP BY a1.album_id
            ) au ON a.id = au.album_id
            WHERE f.user_id = %s
            GROUP BY mi.id, mi.title, mi.duration, a.preview_url, au.authors;
        """
        values = (user_id,)

        try:
            await cursor.execute(query, values)
            result = await cursor.fetchall()
            tracks = []
            for track in result:
                tracks.append({
                    "id": track["id"],
                    "title": track["title"],
                    "duration": track["duration"],
                    "preview_url": track["preview_url"],
                    "inFavorites": True,
                    "authors": json.loads(track["authors"]) if track["authors"] else [],
                })

            print('\n tracks: ', tracks)

            return tracks
        except aiomysql.Error as e:
            print(f"Ошибка: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка получения треков"
            )
        finally:
            await cursor.close()
            connection.close()


async def getTracksHTML(user_id: int):
    connection = await get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Ошибка подключения к базе данных")

    async with connection.cursor(aiomysql.DictCursor) as cursor:
        query = """
            SELECT
                mi.id,
                mi.title,
                mi.duration,
                a.preview_url,
                au.authors
            FROM favorites f
            JOIN media_items mi ON mi.id = f.media_item_id
            JOIN albums a ON mi.album_id = a.id
            LEFT JOIN (
                SELECT
                    a1.album_id,
                    JSON_ARRAYAGG(
                        JSON_OBJECT('id', a1.user_id, 'nickname', u.nickname)
                    ) AS authors
                FROM authors a1
                JOIN users u ON a1.user_id = u.id
                GROUP BY a1.album_id
            ) au ON a.id = au.album_id
            WHERE f.user_id = %s
            GROUP BY mi.id, mi.title, mi.duration, a.preview_url, au.authors;
        """
        values = (user_id,)

        try:
            await cursor.execute(query, values)
            result = await cursor.fetchall()
            tracks = []
            for track in result:
                tracks.append({
                    "id": track["id"],
                    "title": track["title"],
                    "duration": track["duration"],
                    "preview_url": f'http://79.104.192.137/{track["preview_url"].split("/var/www/")[1]}',
                    "inFavorites": True,
                    "authors": json.loads(track["authors"]) if track["authors"] else [],
                })
                print(track)

            # Генерация HTML таблицы
            html_content = """
                    <html>
                    <head>
                        <style>
                            table {
                                width: 100%;
                                border-collapse: collapse;
                                background-color: #fff
                            }
                            th, td {
                                border: 1px solid black;
                                padding: 8px;
                                text-align: left;
                            }
                            th {
                                background-color: #f2f2f2;
                            }
                        </style>
                    </head>
                    <body>
                        <h1>Отчет о понравившемся</h1>
                        <table>
                            <tr>
                                <th>Index</th>
                                <th>ID</th>
                                <th>Title</th>
                                <th>Duration</th>
                                <th>Preview</th>
                                <th>Authors</th>
                            </tr>
                    """
            index = 1
            for track_row in tracks:
                html_content += f"<tr><td>{index}</td><td>{track_row['id']}</td><td>{track_row['title']}</td><td>{track_row['duration']}s</td>"
                html_content += f"<td><img src='{track_row['preview_url']}' width='100' height='100'/></td>"
                html_content += "<td><ul>"
                for author in track_row['authors']:
                    html_content += f"<li>{author['nickname']}</li>"
                html_content += "</ul></td></tr>"
                index += 1
            html_content += "</table></body></html>"

            return html_content
        except aiomysql.Error as e:
            print(f"Ошибка: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка получения треков"
            )
        finally:
            await cursor.close()
            connection.close()
