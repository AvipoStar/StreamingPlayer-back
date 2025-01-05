import json

from fastapi import FastAPI, HTTPException, status
import aiomysql
from config.Database import get_connection  # Assuming this function returns the connection parameters
from models.mediaItem import MediaItem
from models.playlist import createPlaylist, Playlist

app = FastAPI()


async def createPlaylist(playlist: createPlaylist):
    connection = await get_connection()
    if connection is None:
        return None

    async with connection.cursor() as cursor:
        query = "INSERT INTO playlists (name, description) VALUES (%s, %s)"
        values = (playlist.name, playlist.description)

        try:
            await cursor.execute(query, values)
            await connection.commit()
            playlist_id = cursor.lastrowid
            return playlist_id
        except aiomysql.Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка создания плейлиста"
            )
        finally:
            await cursor.close()
            connection.close()


async def deletePlaylist(playlist_id: int):
    connection = await get_connection()
    if connection is None:
        return

    async with connection.cursor() as cursor:
        query = "DELETE FROM playlists WHERE id = %s"
        values = (playlist_id,)

        try:
            await cursor.execute(query, values)
            await connection.commit()
            return True
        except aiomysql.Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка удаления плейлиста"
            )
        finally:
            await cursor.close()
            connection.close()


async def changeName(playlist: createPlaylist):
    connection = await get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection error")

    async with connection.cursor() as cursor:
        query = "UPDATE playlists SET name = %s WHERE id = %s"
        values = (playlist.name, playlist.id)

        try:
            await cursor.execute(query, values)
            await connection.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Playlist not found")
            else:
                return True
        except aiomysql.Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка обновления плейлиста"
            )
        finally:
            await cursor.close()
            connection.close()


async def toggleTrack(track_id: int, playlist_id: int):
    connection = await get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Ошибка подключения к базе данных")

    async with connection.cursor(aiomysql.DictCursor) as cursor:
        try:
            # Проверяем наличие трека в плейлисте
            query = "SELECT * FROM playlist_items WHERE playlist_id = %s AND media_item_id = %s"
            values = (playlist_id, track_id)
            await cursor.execute(query, values)
            track_exists = await cursor.fetchone()

            if track_exists:
                # Удаляем трек из плейлиста
                query = "DELETE FROM playlist_items WHERE playlist_id = %s AND media_item_id = %s"
                await cursor.execute(query, values)
                await connection.commit()

                # Получаем обложку последнего добавленного трека
                query = """
                    SELECT a.preview_url
                    FROM playlist_items pi
                    JOIN media_items mi ON pi.media_item_id = mi.id
                    JOIN albums a ON mi.album_id = a.id
                    WHERE pi.playlist_id = %s
                    ORDER BY pi.id DESC
                    LIMIT 1
                """
                await cursor.execute(query, (playlist_id,))
                result = await cursor.fetchone()
                last_track_preview = result['preview_url'] if result else None

                # Обновляем обложку плейлиста
                if last_track_preview:
                    query = "UPDATE playlists SET preview = %s WHERE id = %s"
                    values = (last_track_preview, playlist_id)
                    await cursor.execute(query, values)
                    await connection.commit()
            else:
                # Добавляем трек в плейлист
                query = "INSERT INTO playlist_items (playlist_id, media_item_id) VALUES (%s, %s)"
                values = (playlist_id, track_id)
                await cursor.execute(query, values)
                await connection.commit()

                # Получаем обложку добавленного трека
                query = """
                    SELECT a.preview_url
                    FROM media_items mi
                    JOIN albums a ON a.id = mi.album_id
                    WHERE mi.id = %s
                """
                await cursor.execute(query, (track_id,))
                track_preview = await cursor.fetchone()

                # Обновляем обложку плейлиста
                if track_preview:
                    query = "UPDATE playlists SET preview = %s WHERE id = %s"
                    values = (track_preview['preview_url'], playlist_id)
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


async def getUserPlaylists(user_id: int):
    connection = await get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection error")

    async with connection.cursor(aiomysql.DictCursor) as cursor:

        try:
            await cursor.execute("SELECT id, name, preview FROM playlists WHERE user_id = %s", (user_id,))
            result = await cursor.fetchall()

            playlists = []
            for playlist in result:
                playlists.append({
                    "id": playlist["id"],  # Используем ключи вместо индексов
                    "title": playlist["name"],
                    "preview_url": playlist["preview"]
                })
            return playlists

        except aiomysql.Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка получения плейлистов пользователя"
            )
        finally:
            await connection.ensure_closed()


async def getPlaylistTracks(playlist_id: int, user_id: int):
    connection = await get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Ошибка подключения к базе данных")

    async with connection.cursor(aiomysql.DictCursor) as cursor:
        try:
            # Получение информации о плейлисте
            await cursor.execute("SELECT id, name, preview FROM playlists WHERE id = %s", (playlist_id,))
            playlist = await cursor.fetchone()
            if not playlist:
                raise HTTPException(status_code=404, detail="Плейлист не найден")

            # Получение треков плейлиста
            query = """
                SELECT mi.id, mi.title, mi.duration, a.preview_url, mi.file_url,
                       CASE
                           WHEN f.media_item_id IS NOT NULL THEN TRUE
                           ELSE FALSE
                       END AS in_favorite,
                       JSON_ARRAYAGG(JSON_OBJECT('id', a1.user_id, 'nickname', u.nickname)) AS authors
                FROM playlist_items pi
                JOIN media_items mi ON pi.media_item_id = mi.id
                JOIN albums a ON mi.album_id = a.id
                JOIN authors a1 ON a.id = a1.album_id
                JOIN users u ON a1.user_id = u.id
                LEFT JOIN favorites f ON mi.id = f.media_item_id AND f.user_id = %s
                WHERE pi.playlist_id = %s
                GROUP BY mi.id, mi.title, mi.duration, a.preview_url, mi.file_url;
            """
            values = (user_id, playlist_id)
            await cursor.execute(query, values)
            result = await cursor.fetchall()

            tracks = []
            for track in result:
                tracks.append({
                    "id": track["id"],
                    "title": track["title"],
                    "duration": track["duration"],
                    "file_url": track["file_url"],
                    "preview_url": track["preview_url"],
                    "inFavorites": track["in_favorite"],
                    "authors": json.loads(track["authors"]) if track["authors"] else [],
                })

            playlist_data = {
                "id": playlist["id"],
                "title": playlist["name"],
                "preview_url": playlist["preview"],
                "tracks": tracks
            }

            return playlist_data
        except aiomysql.Error as e:
            print(f"Ошибка: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка получения треков плейлиста"
            )
        finally:
            await cursor.close()
            connection.close()
