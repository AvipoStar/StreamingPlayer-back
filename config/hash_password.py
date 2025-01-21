from config.Database import get_connection


async def hash_password(password: str) -> str:
    conn = await get_connection()
    try:
        async with conn.cursor() as cursor:
            # Выполняем SQL-запрос для вызова функции HexAndSha256
            await cursor.execute('SELECT HexAndSha256(%s)', (password,))
            hashed_password = await cursor.fetchone()
            print('password', password)
            print('hashed_password', hashed_password)
            return hashed_password[0] if hashed_password else None
    finally:
        conn.close()
