import os

from starlette.responses import StreamingResponse, Response

from config.Database import getConnection


async def stream_music(track_id: int):
    db = getConnection()
    cursor = db.cursor()

    query = f"SELECT file_url FROM media_items WHERE id = {track_id}"
    cursor.execute(query)
    file_path = cursor.fetchone()[0]

    if not os.path.exists(file_path):
        return Response(status_code=404)

    def audio_stream():
        with open(file_path, "rb") as audio_file:
            while chunk := audio_file.read(1024):  # Читаем файл по частям
                yield chunk

    return StreamingResponse(audio_stream(), media_type="audio/mpeg")


async def track_list():
    db = getConnection()
    cursor = db.cursor()

    # Запрос к базе данных для получения информации о треках
    query = """
    SELECT id, title, description, duration, file_url, cover_url 
    FROM media_items
    """

    cursor.execute(query)
    # Извлекаем все строки из результата запроса
    rows = cursor.fetchall()

    # Преобразуем результат в список словарей
    tracks = [
        {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "duration": row[3],
            "file_url": row[4],
            "cover_url": row[5],
        }
        for row in rows
    ]

    # Закрываем соединение
    cursor.close()
    db.close()

    return {"tracks": tracks}
