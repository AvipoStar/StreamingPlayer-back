import aiomysql
from starlette import status
from starlette.exceptions import HTTPException

from config.Database import get_connection


async def search_media(query: str):
    conn = await get_connection()
    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # Поиск авторов
            await cursor.execute("""
                SELECT id, nickname, photo_url
                FROM users
                WHERE nickname LIKE %s
            """, (f"%{query}%",))
            authors = await cursor.fetchall()

            # Поиск медиа-итемов
            await cursor.execute("""
                SELECT mi.id, mi.title, mi.album_id, a.preview_url 
                FROM media_items mi
                JOIN albums a ON a.id = mi.album_id
                WHERE mi.title LIKE %s
            """, (f"%{query}%",))
            media_items = await cursor.fetchall()

            # Поиск альбомов
            await cursor.execute("""
                SELECT id, title, preview_url
                FROM albums
                WHERE title LIKE %s
            """, (f"%{query}%",))
            albums = await cursor.fetchall()

            return {
                "authors": authors,
                "tracks": media_items,
                "albums": albums
            }

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка поиска"
        )
    finally:
        await cursor.close()
        conn.close()
