import json

from fastapi import FastAPI, HTTPException, status

from config.Database import get_connection
from mysql.connector import Error

app = FastAPI()


async def getGenres():
    connection = await get_connection()
    if connection is None:
        return

    cursor = await connection.cursor()
    try:
        await cursor.execute("SELECT id, name, color FROM genres WHERE type = 'music'")
        result = await cursor.fetchall()
        genres = []

        for genre in result:
            genres.append({"id": genre[0], "name": genre[1], "color": genre[2]})

        return genres
    except Error as e:
        print(f"Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ошибка получения жанров"
        )
    finally:
        await cursor.close()
        connection.close()


async def getGenreTracks(genre_id: int, user_id: int):
    connection = await get_connection()
    if connection is None:
        return

    cursor = await connection.cursor()
    try:
        await  cursor.execute("""
        SELECT name, color FROM genres 
        WHERE id = %s""", (genre_id,))
        genre = await cursor.fetchone()

        genre_name, genre_color = genre

        await cursor.execute(""" 
        SELECT
            mi.id,
            mi.title,
            mi.duration,
            mi.file_url,
            a.preview_url,
            JSON_ARRAYAGG(
                JSON_OBJECT('id', au.user_id, 'nickname', u.nickname)
            ) AS authors,
            CASE
                WHEN f.media_item_id IS NOT NULL THEN TRUE
                ELSE FALSE
            END AS in_favorite
        FROM media_items mi
        JOIN albums a ON a.id = mi.album_id
        JOIN authors au ON au.album_id = a.id
        JOIN users u ON u.id = au.user_id
        JOIN mediaItem_genre ig ON mi.id = ig.id_mediaItem
        LEFT JOIN favorites f ON mi.id = f.media_item_id AND f.user_id = %s
        WHERE ig.id_genre = %s
        GROUP BY mi.id, mi.title, mi.duration, mi.file_url, a.preview_url;""", (user_id, genre_id))
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

        return {"genre": {"id": genre_id, "name": genre_name, "color": genre_color},
                "tracks": tracks}
    except Error as e:
        print(f"Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ошибка получения жанров"
        )
    finally:
        await cursor.close()
        connection.close()
