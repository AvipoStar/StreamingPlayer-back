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
        await cursor.execute("SELECT id, name FROM genres WHERE type = 'music'")
        result = await cursor.fetchall()
        genres = []

        for genre in result:
            genres.append({"id": genre[0], "name": genre[1]})

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
