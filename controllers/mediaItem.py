import json
from typing import List

import aiofiles
import aiomysql
from fastapi import FastAPI, HTTPException, status

from mysql.connector import Error
from config.Database import get_connection
from models.mediaItem import MediaItem, CreateMediaItem
from mutagen import File as MutagenFile
from typing import Tuple

app = FastAPI()


# Функция для удаления медиа-элемента
async def removeMediaItem(mediaItemId: int):
    connection = await get_connection()
    async with connection.cursor() as cursor:
        try:
            query = "DELETE FROM media_items WHERE id = %s"
            values = (mediaItemId,)
            await cursor.execute(query, values)
            await connection.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Медиа-элемент не найден")
        except Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка удаления медиа-элемента"
            )
        finally:
            await cursor.close()
            connection.close()


# Функция для обновления медиа-элемента
async def updateMediaItem(mediaItem: MediaItem):
    connection = await get_connection()
    async with connection.cursor() as cursor:
        try:
            query = """
            UPDATE media_items
            SET title = %s, 
                description = %s, 
                cover_url = %s, 
                category_id = %s, 
                release_date = %s, 
                duration = %s, 
                album_id = %s, 
                genre_id = %s, 
                file_size = %s, 
                content_type = %s, 
                file_url = %s
            WHERE id = %s
            """
            values = (
                mediaItem.title,
                mediaItem.description,
                mediaItem.cover_url,
                mediaItem.category_id,
                mediaItem.release_date,
                mediaItem.duration,
                mediaItem.album_id,
                mediaItem.genre_id,
                mediaItem.file_size,
                mediaItem.content_type,
                mediaItem.file_url,
                mediaItem.id
            )
            await cursor.execute(query, values)
            await connection.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Медиа-элемент не найден")
        except Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка обновления медиа-элемента"
            )
        finally:
            await cursor.close()
            connection.close()


async def create_album(title: str, preview: str) -> int:
    conn = await get_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("INSERT INTO albums (title, preview_url, release_date) VALUES (%s, %s, NOW())",
                             (title, preview))
        album_id = cursor.lastrowid
        await conn.commit()
    conn.close()
    return album_id


async def save_media_item(title: str, description: str, file_path: str, album_id: int) -> int:
    print(title, description, file_path, album_id)
    # Получаем размер файла и его длительность
    file_size, duration = await get_file_size_and_duration(file_path)

    # Создаем запись в базе данных в таблицах media_items, albums, authors
    conn = await get_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("""
            INSERT INTO media_items (title, description, category_id, content_type, file_url, album_id, file_size, duration)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            title,
            description,
            2,  # 1-Аудиокнига 2-Трэк
            'mp3',
            file_path,
            album_id,
            file_size,
            duration))
        await conn.commit()
        media_item_id = cursor.lastrowid
    conn.close()
    return media_item_id


async def add_album_to_author(album_id: int, author_id: int) -> int:
    conn = await get_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("INSERT INTO authors (user_id, album_id) VALUES (%s, %s)", (author_id, album_id))
        album_id = cursor.lastrowid
        await conn.commit()
    conn.close()
    return album_id


async def add_genre_to_media_item(media_item_id: int, genre_ids: List[int]):
    conn = await get_connection()
    async with conn.cursor() as cursor:
        try:
            for genre_id in genre_ids:
                await cursor.execute("INSERT INTO mediaItem_genre (id_mediaItem, id_genre) VALUES (%s, %s)",
                                     (media_item_id, genre_id))
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            print(f"Error: {e}")
    conn.close()


async def get_file_size_and_duration(file_path: str) -> Tuple[int, float]:
    # Получаем размер файла
    async with aiofiles.open(file_path, 'rb') as f:
        file_size = (await f.read()).__sizeof__()

    # Получаем длительность аудиофайла
    audio = MutagenFile(file_path)
    duration = audio.info.length

    return file_size, duration


async def addMediaItem(mediaItem: CreateMediaItem, user_id: int) -> int:
    title = mediaItem.title
    description = mediaItem.description
    album_id = mediaItem.album_id
    genre_ids = mediaItem.genre_ids
    file_path = mediaItem.file_path
    preview_path = mediaItem.preview_path

    if album_id == -1:
        # Создаем альбом в базе данных по названию трека и его превью
        album_id = await create_album(title, preview_path)
        await add_album_to_author(album_id, user_id)

    # Создаем запись в таблицу media_items
    media_item_id = await save_media_item(title, description, file_path, album_id)
    await add_genre_to_media_item(media_item_id, genre_ids)
    return media_item_id


async def getMediaItems(user_id: int):
    conn = await get_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT
                    mi.id,
                    mi.title,
                    mi.duration,
                    mi.file_url,
                    a.preview_url,
                    au.authors,
                    CASE
                        WHEN f.media_item_id IS NOT NULL THEN TRUE
                        ELSE FALSE
                    END AS in_favorite
                FROM media_items mi
                JOIN albums a ON a.id = mi.album_id
                LEFT JOIN (
                    SELECT
                        au.album_id,
                        JSON_ARRAYAGG(
                            JSON_OBJECT('id', au.user_id, 'nickname', u.nickname)
                        ) AS authors
                    FROM authors au
                    JOIN users u ON u.id = au.user_id
                    GROUP BY au.album_id
                ) au ON au.album_id = a.id
                LEFT JOIN favorites f ON mi.id = f.media_item_id AND f.user_id = %s
                GROUP BY mi.id, mi.title, mi.duration, mi.file_url, a.preview_url, au.authors;
            """, (user_id,))
            result = await cursor.fetchall()

            tracks = []
            for track in result:
                track_id, title, duration, file_url, preview_url, authors, in_favorite = track
                tracks.append({
                    "id": track_id,
                    "title": title,
                    "duration": duration,
                    "preview_url": preview_url,
                    "file_url": file_url,
                    "inFavorites": in_favorite,
                    "authors": json.loads(authors) if authors else []
                })

            return tracks

    except aiomysql.Error as e:
        await conn.rollback()
        print(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения медиа-элементов"
        )
    finally:
        await cursor.close()
        conn.close()


async def miInPlaylists(track_id: int, user_id: int):
    conn = await get_connection()  # Получение асинхронного соединения
    try:
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT
                    p.id AS playlist_id,
                    p.name AS playlist_name,
                    p.preview,
                    CASE
                        WHEN pi.media_item_id IS NOT NULL THEN TRUE
                        ELSE FALSE
                    END AS has_media_item
                FROM
                    StreamingPlayer.playlists p
                LEFT JOIN StreamingPlayer.playlist_items pi ON p.id = pi.playlist_id AND pi.media_item_id = %s
                WHERE p.user_id = %s
            """, (track_id, user_id))
            result = await cursor.fetchall()

            playlists = []
            for playlist in result:
                playlist_id, playlist_name, preview, has_media_item = playlist
                playlists.append({
                    "id": playlist_id,
                    "title": playlist_name,
                    "preview_url": preview,
                    "has_media_item": has_media_item,
                })

            return playlists

    except aiomysql.Error as e:
        await conn.rollback()
        print(f"Database error: {e}")
        raise

    finally:
        await conn.ensure_closed()


async def getMediaItemDetails(media_item_id: int):
    conn = await get_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT
                  mi.id,
                  mi.title,
                  mi.duration,
                  mi.file_url,
                  a.preview_url,
                  mi.description,
                  (SELECT JSON_ARRAYAGG(
                      JSON_OBJECT('id', ig.id_genre, 'title', g.name)
                  ) FROM mediaItem_genre ig
                  JOIN genres g ON ig.id_genre = g.id
                  WHERE mi.id = ig.id_mediaItem) AS genres,
                  (SELECT JSON_ARRAYAGG(
                      JSON_OBJECT('id', au.user_id, 'nickname', u.nickname)
                  ) FROM authors au
                  JOIN users u ON u.id = au.user_id
                  WHERE au.album_id = a.id) AS authors
                FROM media_items mi
                JOIN albums a ON a.id = mi.album_id
                WHERE mi.id = %s
                GROUP BY mi.id, mi.title, mi.duration, mi.file_url, a.preview_url, mi.description;
            """, (media_item_id,))
            result = await cursor.fetchone()

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ошибка получения данных трэка"
                )

            track_id, title, duration, file_url, preview_url, description, genres, authors = result
            track = {
                "id": track_id,
                "title": title,
                "duration": duration,
                "preview_url": preview_url,
                "file_url": file_url,
                "authors": json.loads(authors) if authors else [],
                "description": description,
                "genres": json.loads(genres) if genres else []
            }

            return track

    except aiomysql.Error as e:
        await conn.rollback()
        print(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения медиа-элементов"
        )
    finally:
        await cursor.close()
        conn.close()


async def get_latest_tracks(user_id: int):
    conn = await get_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute("""
               SELECT
                    mi.id,
                    mi.title,
                    mi.duration,
                    mi.file_url,
                    a.preview_url,
                    au.authors,
                    CASE
                        WHEN f.media_item_id IS NOT NULL THEN TRUE
                        ELSE FALSE
                    END AS in_favorite
                FROM media_items mi
                JOIN albums a ON a.id = mi.album_id
                LEFT JOIN (
                    SELECT
                        au.album_id,
                        JSON_ARRAYAGG(
                            JSON_OBJECT('id', au.user_id, 'nickname', u.nickname)
                        ) AS authors
                    FROM authors au
                    JOIN users u ON u.id = au.user_id
                    GROUP BY au.album_id
                ) au ON au.album_id = a.id
                LEFT JOIN favorites f ON mi.id = f.media_item_id AND f.user_id = %s
                GROUP BY mi.id, mi.title, mi.duration, mi.file_url, a.preview_url, au.authors
                ORDER BY a.release_date DESC
                LIMIT 10;
            """, (user_id,))
            result = await cursor.fetchall()

            tracks = []
            for track in result:
                track_id, title, duration, file_url, preview_url, authors, in_favorite = track
                tracks.append({
                    "id": track_id,
                    "title": title,
                    "duration": duration,
                    "preview_url": preview_url,
                    "file_url": file_url,
                    "in_favorite": in_favorite,
                    "authors": json.loads(authors) if authors else []
                })

            return tracks

    except aiomysql.Error as e:
        await conn.rollback()
        print(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения медиа-элементов"
        )
    finally:
        await cursor.close()
        conn.close()


async def get_listening_history(user_id: int):
    conn = await get_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT
                    h.id,
                    h.media_item_id,
                    h.listened_at,
                    mi.title,
                    mi.duration,
                    mi.file_url,
                    a.preview_url,
                    au.authors
                FROM history h
                JOIN media_items mi ON mi.id = h.media_item_id
                JOIN albums a ON a.id = mi.album_id
                LEFT JOIN (
                    SELECT
                        au.album_id,
                        JSON_ARRAYAGG(
                            JSON_OBJECT('id', au.user_id, 'nickname', u.nickname)
                        ) AS authors
                    FROM authors au
                    JOIN users u ON u.id = au.user_id
                    GROUP BY au.album_id
                ) au ON au.album_id = a.id
                WHERE h.user_id = %s
                ORDER BY h.listened_at DESC;
            """, (user_id,))
            result = await cursor.fetchall()

            history = []
            for item in result:
                id, media_item_id, listened_at, title, duration, file_url, preview_url, authors = item
                history.append({
                    "id": id,
                    "media_item_id": media_item_id,
                    "listened_at": listened_at.isoformat(),
                    "title": title,
                    "duration": duration,
                    "file_url": file_url,
                    "preview_url": preview_url,
                    "authors": json.loads(authors) if authors else []
                })

            return history

    except aiomysql.Error as e:
        await conn.rollback()
        print(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения истории прослушивания"
        )
    finally:
        await cursor.close()
        conn.close()
