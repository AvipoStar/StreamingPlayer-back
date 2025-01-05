import aiomysql
import mysql.connector


def getConnection():
    try:
        db = mysql.connector.connect(
            host='79.104.192.137',
            port='3306',
            user='streamer',
            password='3103',
            database='StreamingPlayer'
        )
        return db
    except Exception as e:
        print(f"Ошибка при подключении к базе данных: {e}")
        return None


DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'streamer',
    'password': '3103',
    'db': 'StreamingPlayer'
}


async def get_connection():
    return await aiomysql.connect(**DATABASE_CONFIG)
