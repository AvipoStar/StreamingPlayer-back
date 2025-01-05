from fastapi import APIRouter

from controllers.admin import get_table_row_counts

router = APIRouter()


@router.get('/tablesData', tags=["Admin"])
async def get_tablesData():
    tables = await get_table_row_counts()
    return tables
