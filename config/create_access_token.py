from datetime import datetime, timedelta
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

import jwt

SECRET_KEY = "stream"
ALGORITHM = "HS256"


def createAccessToken(email: str, user_id: int):
    expire = datetime.utcnow() + timedelta(minutes=96720)
    payload = {
        "email": email,
        "user_id": user_id,
        "exp": expire
    }
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decodeAccessToken(token: str):
    try:
        # Декодирование токена
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token
    except ExpiredSignatureError:
        raise Exception("Токен истек")
    except InvalidTokenError:
        raise Exception("Недействительный токен")


