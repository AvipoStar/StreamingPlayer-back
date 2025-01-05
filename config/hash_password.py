import hashlib
import time


async def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()
