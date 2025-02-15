from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from controllers.admin import get_table_row_counts, export_author_to_file, getAuthorStats, getAuthorStatsCSV, \
    getGenreStatistic, getUserListenCount, getReporAuthors, getReporGenres, getPivotTableReport
from models.simpleValues import DatePeriod

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


@router.get("/getReporAuthors", tags=["Admin"])
async def get_repor_authors():
    result = await getReporAuthors()
    return result


@router.get("/getReporGenres", tags=["Admin"])
async def get_repor_genres():
    result = await getReporGenres()
    return result


@router.post("/getReporPivotTable", tags=["Admin"])
async def get_pivot_table_report(value: DatePeriod):
    result = await getPivotTableReport(value.dateStart, value.dateEnd)
    return result














@router.post("/")
async def test_router():
    return 'hello world'
