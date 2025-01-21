from typing import Optional

from fastapi import APIRouter, Query

from controllers.admin import get_table_row_counts, export_author_to_file, getAuthorStats, getAuthorStatsCSV, \
    getGenreStatistic, getUserListenCount

router = APIRouter()


@router.get('/tablesData', tags=["Admin"])
async def get_tablesData():
    tables = await get_table_row_counts()
    return tables


@router.get("/exportAuthorData/{author_id}", tags=["Admin"])
async def export_users_to_file(author_id: int):
    result = await export_author_to_file(author_id)
    return result


@router.get("/getAuthorStats", tags=["Admin"])
async def get_author_stats(period: Optional[str] = Query(None)):
    result = await getAuthorStats(period)
    return result


@router.get("/getAuthorStatsCSV", tags=["Admin"])
async def get_author_stats_csv(author_id: int, period: Optional[str] = Query(None)):
    result = await getAuthorStatsCSV(author_id, period)
    return result


@router.get("/getGenreStatistic", tags=["Admin"])
async def get_genre_statistic():
    result = await getGenreStatistic()
    return result


@router.get("/getUserListenCount", tags=["Admin"])
async def get_user_listen_count():
    result = await getUserListenCount()
    return result
