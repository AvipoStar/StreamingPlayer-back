from fastapi import FastAPI, APIRouter, UploadFile

from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from routers.mediaItem import router as mediaItem_router
from routers.album import router as album_router
from routers.author import router as author_router
from routers.login import router as auth_router
from routers.registration import router as reg_router
from routers.userData import router as user_router
from routers.playlist import router as playlist_router
from routers.favorites import router as favorites_router
from routers.userSettings import router as userSettings_router
from routers.player import router as player_router
from routers.genre import router as genre_router
from routers.file import router as file_router
from routers.admin import router as admin_router
from routers.search import router as search_router
from routers.superAdmin import router as superAdmin_router

app = FastAPI()

# Добавляем middleware для обработки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Здесь можно указать список допустимых источников запросов
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все HTTP методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

# Обслуживание статических файлов
# app.mount("/uploads", StaticFiles(directory="/var/www/uploads"), name="uploads")

app.include_router(
    router=auth_router,
    prefix='/auth'
)
app.include_router(
    router=reg_router,
    prefix='/reg'
)
app.include_router(
    router=user_router,
    prefix='/user'
)
app.include_router(
    router=mediaItem_router,
    prefix='/mediaItem'
)

app.include_router(
    router=album_router,
    prefix='/album'
)
app.include_router(
    router=file_router,
    prefix='/file'
)
app.include_router(
    router=author_router,
    prefix='/author'
)

app.include_router(
    router=playlist_router,
    prefix='/playlist'
)

app.include_router(
    router=favorites_router,
    prefix='/favorites'
)

app.include_router(
    router=userSettings_router,
    prefix='/userSettings'
)
app.include_router(
    router=player_router,
    prefix='/player'
)
app.include_router(
    router=genre_router,
    prefix='/genre'
)
app.include_router(
    router=admin_router,
    prefix='/admin'
)
app.include_router(
    router=search_router,
    prefix='/search'
)
app.include_router(
    router=superAdmin_router,
    prefix='/superAdmin'
)
