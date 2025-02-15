import csv
import io
import json
import os
from datetime import date, timedelta

import aiomysql
import pandas as pd
from starlette import status
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse, StreamingResponse

from config.Database import get_connection
from config.convertDate import convertDate
from config.convertImgPath import convertImgPath


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


async def get_listening_report(start_date: date, end_date: date):
    conn = await get_connection()
    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            query = """
                SELECT
                    c.name AS category,
                    COUNT(h.id) AS total_listens,
                    JSON_ARRAYAGG(
                        JSON_OBJECT(
                            'media_item_id', mi.id,
                            'title', mi.title,
                            'duration', mi.duration,
                            'file_url', mi.file_url,
                            'preview_url', a.preview_url,
                            'authors', au.authors,
                            'listened_at', h.listened_at
                        )
                    ) AS details
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
                JOIN categories c ON c.id = mi.category_id
                WHERE h.listened_at BETWEEN %s AND %s
                GROUP BY c.name;
            """
            await cursor.execute(query, (start_date, end_date))
            result = await cursor.fetchall()

            listening_reports = []
            for row in result:
                listening_reports.append({
                    "category": row["category"],
                    "total_listens": row["total_listens"],
                    "details": json.loads(row["details"]) if row["details"] else []
                })

            return listening_reports

    except aiomysql.Error as e:
        await conn.rollback()
        print(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения отчета"
        )
    finally:
        await cursor.close()
        conn.close()


async def getAuthorStats(period: str):
    conn = await get_connection()
    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            query = """
                SELECT
                    au.user_id AS author_id,
                    u.nickname AS author_name,
                    COUNT(h.id) AS total_listens
                FROM history h
                JOIN media_items mi ON mi.id = h.media_item_id
                JOIN albums a ON a.id = mi.album_id
                JOIN authors au ON au.album_id = a.id
                JOIN users u ON u.id = au.user_id
            """
            if period:
                today = date.today()
                if period == "day":
                    start_date = today
                elif period == "week":
                    start_date = today - timedelta(days=7)
                elif period == "month":
                    start_date = today - timedelta(days=30)
                elif period == "half_year":
                    start_date = today - timedelta(days=180)
                elif period == "year":
                    start_date = today - timedelta(days=365)
                query += f" WHERE h.listened_at >= '{start_date}'"
            query += " GROUP BY au.user_id, u.nickname;"
            await cursor.execute(query)
            result = await cursor.fetchall()

            author_stats = []
            for row in result:
                author_stats.append({
                    "author_id": row["author_id"],
                    "author_name": row["author_name"],
                    "total_listens": row["total_listens"]
                })

            return author_stats

    except aiomysql.Error as e:
        await conn.rollback()
        print(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения статистики"
        )
    finally:
        await cursor.close()
        conn.close()


async def getAuthorStatsCSV(author_id: int, period: str = None):
    conn = await get_connection()
    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # Получение даты регистрации автора
            query_registration = """
                SELECT created_at AS registration_date
                FROM users
                WHERE id = %s;
            """
            await cursor.execute(query_registration, (author_id,))
            registration_date = await cursor.fetchone()

            # Получение общего количества треков автора
            query_tracks = """
                SELECT COUNT(mi.id) AS total_tracks
                FROM media_items mi
                JOIN albums a ON a.id = mi.album_id
                JOIN authors au ON au.album_id = a.id
                WHERE au.user_id = %s;
            """
            await cursor.execute(query_tracks, (author_id,))
            total_tracks = await cursor.fetchone()

            # Получение общего количества альбомов автора
            query_albums = """
                SELECT COUNT(a.id) AS total_albums
                FROM albums a
                JOIN authors au ON au.album_id = a.id
                WHERE au.user_id = %s;
            """
            await cursor.execute(query_albums, (author_id,))
            total_albums = await cursor.fetchone()

            # Получение общего количества прослушиваний треков автора
            query_listens = """
                SELECT
                    au.user_id AS author_id,
                    u.nickname AS author_name,
                    COUNT(h.id) AS total_listens
                FROM history h
                JOIN media_items mi ON mi.id = h.media_item_id
                JOIN albums a ON a.id = mi.album_id
                JOIN authors au ON au.album_id = a.id
                JOIN users u ON u.id = au.user_id
                WHERE au.user_id = %s
            """
            if period:
                today = date.today()
                if period == "day":
                    start_date = today
                elif period == "week":
                    start_date = today - timedelta(days=7)
                elif period == "month":
                    start_date = today - timedelta(days=30)
                elif period == "half_year":
                    start_date = today - timedelta(days=180)
                elif period == "year":
                    start_date = today - timedelta(days=365)
                query_listens += f" AND h.listened_at >= '{start_date}'"
            query_listens += " GROUP BY au.user_id, u.nickname;"
            await cursor.execute(query_listens, (author_id,))
            result = await cursor.fetchall()

            # Получение количества треков по жанрам
            query_genres = """
                SELECT g.name AS genre, COUNT(mi.id) AS track_count
                FROM media_items mi
                JOIN albums a ON a.id = mi.album_id
                JOIN authors au ON au.album_id = a.id
                JOIN mediaItem_genre mig ON mi.id = mig.id_mediaItem
                JOIN genres g ON mig.id_genre = g.id
                WHERE au.user_id = %s
                GROUP BY g.name;
            """
            await cursor.execute(query_genres, (author_id,))
            genre_counts = await cursor.fetchall()

            if not result or not registration_date or not total_tracks or not total_albums:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Статистика для данного автора не найдена"
                )

            # Создание CSV файла
            output = io.StringIO()
            csv_writer = csv.writer(output)
            csv_writer.writerow(
                ["ID author", "Nickname", "Registration date", "Total tracks count", "Total albums count",
                 "Total listens count"])
            for row in result:
                csv_writer.writerow([
                    row["author_id"],
                    row["author_name"],
                    registration_date["registration_date"],
                    total_tracks["total_tracks"],
                    total_albums["total_albums"],
                    row["total_listens"]
                ])

            # Добавление количества треков по жанрам
            csv_writer.writerow([])  # Пустая строка для разделения
            csv_writer.writerow(["Genre", "Tracks count"])
            for genre in genre_counts:
                csv_writer.writerow([genre["genre"], genre["track_count"]])

            output.seek(0)

            return StreamingResponse(output, media_type="text/csv",
                                     headers={"Content-Disposition": "attachment; filename=author_stats.csv"})

    except aiomysql.Error as e:
        await conn.rollback()
        print(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения статистики"
        )
    finally:
        await cursor.close()
        conn.close()


async def getGenreStatistic():
    conn = await get_connection()
    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            query = """
                SELECT g.name AS genre, COUNT(h.id) AS listen_count
                FROM history h
                JOIN media_items mi ON h.media_item_id = mi.id
                JOIN mediaItem_genre mig ON mi.id = mig.id_mediaItem
                JOIN genres g ON mig.id_genre = g.id
                GROUP BY g.name;
            """
            await cursor.execute(query)
            result = await cursor.fetchall()

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Статистика по жанрам не найдена"
                )

            return result

    except aiomysql.Error as e:
        await conn.rollback()
        print(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения статистики по жанрам"
        )
    finally:
        await cursor.close()
        conn.close()


async def getUserListenCount():
    conn = await get_connection()
    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            query = """
                    SELECT decrypt_data(u.name) AS user_name, COUNT(h.id) AS listen_count
                    FROM history h
                    JOIN users u ON h.user_id = u.id
                    GROUP BY u.name;
                """
            await cursor.execute(query)
            result = await cursor.fetchall()

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Статистика по пользователям не найдена"
                )

            return result

    except aiomysql.Error as e:
        await conn.rollback()
        print(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения статистики по пользователям"
        )
    finally:
        await cursor.close()
        conn.close()


async def getReporAuthors():
    connection = await get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Ошибка подключения к базе данных")

    async with connection.cursor(aiomysql.DictCursor) as cursor:
        try:
            # Получение данных авторов
            await cursor.execute('''SELECT u.id, u.nickname FROM authors a
                                        JOIN users u ON a.user_id = u.id
                                        GROUP BY u.id;
                                        ''')
            authors = await cursor.fetchall()

            author_result = []
            for author in authors:
                # Получение альбомов для каждого автора
                await cursor.execute('''
                            SELECT a1.id, a1.title, a1.release_date, a1.preview_url FROM albums a1
                            JOIN authors a ON a.album_id = a1.id
                            WHERE a.user_id = %s;''', (author['id'],))
                albums = await cursor.fetchall()

                album_result = []
                for album in albums:
                    # Получение треков для каждого альбома
                    await cursor.execute('''
                                SELECT mi.title, mi.duration, GROUP_CONCAT(g.name ORDER BY g.name SEPARATOR ', ') AS genres
                                FROM media_items mi
                                JOIN mediaItem_genre ig ON mi.id = ig.id_mediaItem
                                JOIN genres g ON ig.id_genre = g.id
                                WHERE mi.album_id = %s
                                GROUP BY mi.id;''', (album['id'],))
                    tracks = await cursor.fetchall()
                    album_result.append(
                        {'album_title': album['title'],
                         'release_date': convertDate(album['release_date']),
                         "preview_url": convertImgPath(album["preview_url"]),
                         'tracks': tracks})

                author_result.append({
                    'author_id': author['id'],
                    'author_nickname': author['nickname'],
                    'albums': album_result
                })

            # Генерация HTML таблицы
            html_content = """
                    <html>
                    <head>
                        <style>
                            body {
                                font-family: Arial, sans-serif;
                            }
                            .table {
                                border: 1px solid black;
                                width: 100%;
                                border-collapse: collapse;
                                background-color: #fff;
                            }
                            .table-row {
                                display: flex;
                                flex-direction: row;
                                align-items: flex-start;
                                border-bottom: 1px solid black;
                            }
                            .index {
                                font-weight: bold;
                                margin: 10px;
                                width: 50px;
                                text-align: center;
                            }
                            .author-row {
                                display: flex;
                                flex-direction: column;
                                border-left: 1px solid black;
                                text-align: left;
                                width: 100%;
                            }
                            .album-row {
                                display: flex;
                                flex-direction: row;
                                text-align: left;
                                width: 100%;
                                align-items: flex-start;
                                border-bottom: 1px solid #000;
                            }
                            .album-name {
                                display: flex;
                                flex-direction: column;
                                align-items: center;
                                gap: 5px;
                                padding: 10px;
                                border-right: 1px solid #000;
                                width: 260px;
                            }
                            .album-cover {
                                width: 70px;
                            }
                            table {
                                text-align: left;
                                border-collapse: collapse;
                                width: 100%;
                            }
                            .author-name,
                            .track-name {
                                padding: 5px;
                                border-bottom: 1px solid #000;
                            }
                            th,
                            td {
                                padding-right: 5px;
                                border: 1px solid #000;
                            }
                            th:first-child, td:first-child{
                                width: 350px;
                            }
                        </style>
                    </head>
                    <body>
                        <h1>Отчет по авторам</h1>
                        <div class="table">
                """

            author_index = 1
            for author in author_result:
                html_content += f"<div class='table-row'>" \
                                f"<div class='index'>{author_index}.</div>" \
                                f"<div class='author-row'>" \
                                f"<div class='author-name'><strong>Автор: {author['author_nickname']}</strong></div>"
                for album in author['albums']:
                    html_content += f"<div class='album-row'>" \
                                    f"<div class='album-name'>" \
                                    f"<img class='album-cover' src='{album['preview_url']}' alt='Нет фото'/>" \
                                    f"<strong>{album['album_title']}</strong>" \
                                    f"<div><strong>Выпущен:</strong> {album['release_date']}</div>" \
                                    f"</div>" \
                                    f"<table>" \
                                    f"<thead>" \
                                    f"<tr>" \
                                    f"<th>Название</th>" \
                                    f"<th>Продолжительность</th>" \
                                    f"<th>Жанры</th>" \
                                    f"</tr>" \
                                    f"</thead>" \
                                    f"<tbody>"
                    for track in album['tracks']:
                        html_content += f"<tr>" \
                                        f"<td>{track['title']}</td>" \
                                        f"<td>{track['duration']} сек.</td>" \
                                        f"<td>{track['genres']} сек.</td>" \
                                        f"</tr>"
                    html_content += f"</tbody>" \
                                    f"</table>" \
                                    f"</div>"
                html_content += f"</div></div>"
                author_index += 1
            html_content += "</div></body></html>"

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


async def getReporGenres():
    connection = await get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Ошибка подключения к базе данных")

    async with connection.cursor(aiomysql.DictCursor) as cursor:
        try:
            # Получение данных жанров
            await cursor.execute('''SELECT id, name FROM genres;''')
            genres = await cursor.fetchall()

            genre_result = []
            for genre in genres:
                # Получение треков для каждого жанра и их количества прослушиваний
                await cursor.execute('''
                                SELECT mi.title, mi.duration, COUNT(h.id) as listen_count
                                FROM media_items mi
                                JOIN mediaItem_genre mig ON mi.id = mig.id_mediaItem
                                JOIN genres g ON mig.id_genre = g.id
                                LEFT JOIN history h ON mi.id = h.media_item_id
                                WHERE g.id = %s
                                GROUP BY mi.title, mi.duration;''', (genre['id'],))
                tracks = await cursor.fetchall()

                total_listens = sum(track['listen_count'] for track in tracks)

                genre_result.append({
                    'genre_id': genre['id'],
                    'genre_name': genre['name'],
                    'total_listens': total_listens,
                    'tracks': tracks
                })

            # Генерация HTML таблицы
            html_content = """
                    <html>
                    <head>
                        <style>
                            .table {
                                border: 1px solid black;
                                width: 100%;
                                background-color: #fff;
                                display: flex;
                                flex-direction: column;
                              }
                            .table-row {
                                display: flex;
                                flex-direction: row;
                                align-items: flex-start;
                                border: 1px solid black;
                                border-collapse: collapse;
                            }
                            .index
                            {
                                width: 250px;
                                padding: 5px;
                            }
                            .genre-row {
                                display: flex;
                                flex-direction: column;
                                text-align: left;
                                align-items: stretch;
                                width: 100%;
                            }
                            .genre-name {
                                display: flex;
                                flex-direction: row;
                                gap: 10px;
                            }
                            .track-row {
                                display: flex;
                                flex-direction: row;
                                gap: 10px;
                                margin-left: 20px;
                                border: 1px solid black;
                                padding: 8px;
                                text-align: left;
                            }
                            table {
                                border-collapse: collapse;
                            }
                            td,
                            th {
                                border: 1px solid #000;
                            }
                            th:first-child, td:first-child{
                                width: 350px;
                            }
                        </style>
                    </head>
                    <body>
                        <h1>Отчет по жанрам</h1>
                        <div class="table">
                """

            genre_index = 1
            for genre in genre_result:
                html_content += f"<div class='table-row'>" \
                                f"<div class='index'>" \
                                f"{genre_index}. " \
                                f"<strong>Жанр: {genre['genre_name']}</strong>" \
                                f"<div>Количество прослушиваний: {genre['total_listens']}</div>" \
                                f"</div>" \
                                f"<div class='genre-row'>" \
                                f"<table>" \
                                f"<thead>" \
                                f"<tr>" \
                                f"<th>Название</th>" \
                                f"<th>Количество прослушиваний</th>" \
                                f"<th>Длительность</th>" \
                                f"</tr>" \
                                f"</thead>" \
                                f"<tbody>"
                for track in genre['tracks']:
                    html_content += f"<tr>" \
                                    f"<td>{track['title']}</td>" \
                                    f"<td>{track['listen_count']}</td>" \
                                    f"<td>{track['duration']} сек.</td>" \
                                    f"</tr>"
                html_content += f"</tbody>" \
                                f"</table>" \
                                f"</div>" \
                                f"</div>"
                genre_index += 1
            html_content += "</div></body></html>"

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

async def getPivotTableReport(dateStart: str, dateEnd: str):
    connection = await get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Ошибка подключения к базе данных")

    async with connection.cursor(aiomysql.DictCursor) as cursor:
        try:
            # Получение данных жанров с фильтрацией по датам
            await cursor.execute('''
                SELECT
                    v.release_date,
                    COUNT(IF(v.name = 'Поп', v.id, NULL)) AS 'Поп',
                    COUNT(IF(v.name = 'Хип-хоп', v.id, NULL)) AS 'Хип-хоп',
                    COUNT(IF(v.name = 'Рок', v.id, NULL)) AS 'Рок',
                    COUNT(IF(v.name = 'Классика', v.id, NULL)) AS 'Классика'
                FROM
                    view1 v
                WHERE
                    v.release_date BETWEEN %s AND %s
                GROUP BY
                    v.release_date;
            ''', (dateStart, dateEnd))
            pivot_table = await cursor.fetchall()

            print('pivot_table', pivot_table)

            # Генерация HTML таблицы
            html_content = """
                <html>
                <head>
                <style>
                    table {
                        border-collapse: collapse;
                        background-color: #fff;
                    }
                    th, td {
                        border: 1px solid #000;
                        text-align: center;
                        padding: 5px;
                    }
                </style>
                </head>
                <body>
                    <h1>Отчет по жанрам</h1>
                    <table>
                        <thead>
                            <tr>
                                <th>Дата</th>
                                <th>Поп</th>
                                <th>Хип-хоп</th>
                                <th>Рок</th>
                                <th>Классика</th>
                            </tr>
                        </thead>
                        <tbody>
            """

            for row in pivot_table:
                html_content += f"<tr>"
                html_content += f'<td>{row["release_date"]}</td>'
                html_content += f'<td>{row["Поп"]}</td>'
                html_content += f'<td>{row["Хип-хоп"]}</td>'
                html_content += f'<td>{row["Рок"]}</td>'
                html_content += f'<td>{row["Классика"]}</td>'
                html_content += f'</tr>'

            html_content += "</tbody></table></body></html>"

            return html_content
        except aiomysql.Error as e:
            print(f"Ошибка: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка получения данных"
            )
        finally:
            await cursor.close()
            connection.close()


