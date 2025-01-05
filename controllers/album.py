import aiomysql
from fastapi import FastAPI, HTTPException, status, UploadFile

from config.Database import getConnection, get_connection
from models.album import CreateAlbum, Album

app = FastAPI()


async def addAlbum(album: CreateAlbum, user_id: int):
    connection = await get_connection()

    if connection is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection error")

    async with connection.cursor() as cursor:
        try:
            await cursor.execute("INSERT INTO albums (title, release_date, preview_url) VALUES (%s, %s, %s)",
                                 (album.title, album.release_date, album.preview_url))
            await connection.commit()

            album_id = cursor.lastrowid
            await cursor.execute("INSERT INTO authors (user_id, album_id) VALUES (%s, %s)", (user_id, album_id))
            await connection.commit()
        except aiomysql.Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка добавления альбома"
            )
        finally:
            await cursor.close()
            connection.close()


# Функция для удаления альбома
async def removeAlbum(albumId: int):
    connection = await get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection error")

    async with connection.cursor() as cursor:
        try:
            await cursor.execute("DELETE FROM albums WHERE id = %s", (albumId,))
            await connection.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Альбом не найден")
        except aiomysql.Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка удаления альбома"
            )
        finally:
            await cursor.close()
            connection.close()


# Функция для обновления альбома
async def updateAlbum(album: Album, preview: UploadFile):
    connection = await getConnection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection error")

    async with connection.cursor() as cursor:
        try:
            query = """
                UPDATE albums
                SET title = %s, release_date = %s, preview_url = %s
                WHERE id = %s
                """
            values = (
                album.title,
                album.release_date,
                preview,
                album.id
            )
            await cursor.execute(query, values)
            await connection.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Альбом не найден")
        except aiomysql.Error as e:
            print(f"Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка обновления альбома"
            )
        finally:
            await cursor.close()
            connection.close()


async def getAlbumTracks(album_id: int, user_id: int):
    try:
        connection = await get_connection()
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ошибка подключения к базе данных"
        )

    async with connection.cursor() as cursor:
        try:

            await cursor.execute("""SELECT a.title, a.preview_url FROM albums a WHERE a.id = %s""", (album_id,))
            result = await cursor.fetchone()

            album_title, album_preview_url = result

            await cursor.execute("""
                                SELECT mi.id, mi.title, mi.duration,
                                CASE
                                    WHEN f.user_id IS NOT NULL THEN TRUE
                                    ELSE FALSE
                                END AS in_favorite
                                FROM media_items mi 
                                JOIN albums a ON mi.album_id = a.id
                                LEFT JOIN favorites f ON mi.id = f.media_item_id AND f.user_id = %s
                                WHERE a.id = %s
                """, (user_id, album_id))
            result = await cursor.fetchall()

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Трэки не найдены"
                )

            tracks = [{
                "id": row[0],
                "title": row[1],
                "duration": row[2],
                "inFavorites": row[3]}
                for row in result]

            print('\n tracks: ', tracks)

            return {
                "album": {
                    "id": album_id,
                    "title": album_title,
                    "preview_url": album_preview_url,
                    "tracks": tracks}
            }

        except aiomysql.Error as e:
            print(f"Database error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка выполнения запроса к базе данных"
            )
        finally:
            await cursor.close()
            connection.close()
