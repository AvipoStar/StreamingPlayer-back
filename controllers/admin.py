import aiomysql

from config.Database import get_connection


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
