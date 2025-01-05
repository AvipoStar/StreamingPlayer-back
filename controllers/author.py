import json

import aiomysql
from fastapi import FastAPI, HTTPException, status

from config.Database import get_connection

app = FastAPI()


async def getAuthors(search: str):
    conn = await get_connection()
    try:
        async with conn.cursor() as cursor:
            try:
                query = "SELECT id, nickname FROM users WHERE nickname LIKE %s"
                search_param = f"%{search}%"
                await cursor.execute(query, (search_param,))
                result = await cursor.fetchall()

                if cursor.rowcount == 0:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Авторы не найдены")

                authors = []
                for author in result:
                    authors.append({"id": author[0], "nickname": author[1]})

                return authors
            except aiomysql.Error as e:
                print(f"Error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ошибка получения авторов"
                )
            finally:
                await cursor.close()
                conn.close()
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения авторов"
        )


async def getTracks(author_id: int, user_id: int):
    conn = await get_connection()
    try:
        async with conn.cursor() as cursor:
            try:
                query = """
                    SELECT mi.id, mi.title, mi.duration, a.preview_url,
                        CASE
                           WHEN f.media_item_id IS NOT NULL THEN TRUE
                           ELSE FALSE
                       END AS in_favorite,
                       JSON_ARRAYAGG(JSON_OBJECT('id', a1.user_id, 'nickname', u.nickname)) AS authors
                    FROM media_items mi
                    JOIN albums a ON mi.album_id = a.id
                    JOIN authors a1 ON a.id = a1.album_id
                    JOIN users u ON a1.user_id = u.id
                    LEFT JOIN favorites f ON mi.id = f.media_item_id AND f.user_id = %s
                    WHERE a1.user_id = %s
                    GROUP BY mi.id, mi.title, mi.duration, a.preview_url;
                """
                await cursor.execute(query, (user_id, author_id))
                result = await cursor.fetchall()

                if cursor.rowcount == 0:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Трэки не найдены")

                tracks = []
                for track in result:
                    track_id, title, duration, preview_url, in_favorite, authors_json = track
                    authors = json.loads(authors_json)
                    tracks.append({
                        "id": track_id,
                        "title": title,
                        "duration": duration,
                        "preview_url": preview_url,
                        "inFavorites": in_favorite,
                        "authors": authors
                    })
                return tracks

            except aiomysql.Error as e:
                print(f"Error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ошибка получения трэков"
                )
            finally:
                await cursor.close()
                conn.close()
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения трэков"
        )


async def getAlbums(author_id: int):
    conn = await get_connection()
    try:
        async with conn.cursor() as cursor:
            try:
                query = """
                SELECT a1.id, a1.title, a1.preview_url FROM users u
                JOIN authors a ON u.id = a.user_id
                JOIN albums a1 ON a.album_id = a1.id
                WHERE u.id = %s;
                """
                await cursor.execute(query, (author_id,))
                result = await cursor.fetchall()

                if cursor.rowcount == 0:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Альбомы не найдены")

                albums = []
                for album in result:
                    album_id, album_title, preview_url = album
                    albums.append({
                        "id": album_id,
                        "title": album_title,
                        "preview_url": preview_url,
                    })
                return albums

            except aiomysql.Error as e:
                print(f"Error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ошибка получения альбомов"
                )
            finally:
                await cursor.close()
                conn.close()
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения альбомов"
        )


async def getAuthorInfo(author_id: int):
    conn = await get_connection()
    try:
        async with conn.cursor() as cursor:
            try:
                query = """
                    SELECT u.nickname, u.photo_url FROM users u
                    JOIN authors a ON u.id = a.user_id
                    WHERE u.id = %s
                    GROUP BY u.id
                    """
                await cursor.execute(query, (author_id,))
                result = await cursor.fetchone()

                if not result:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Автор не найден")

                nickname, photo_url = result

                return {
                    "id": author_id,
                    "nickname": nickname,
                    "photo_url": photo_url
                }

            except aiomysql.Error as e:
                print(f"Error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ошибка получения данных автора"
                )
            finally:
                await cursor.close()
                conn.close()
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения данных автора"
        )
