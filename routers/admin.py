from fastapi import APIRouter

from controllers.admin import get_table_row_counts, export_author_to_file

router = APIRouter()


@router.get('/tablesData', tags=["Admin"])
async def get_tablesData():
    tables = await get_table_row_counts()
    return tables


@router.get("/exportAuthorData/{author_id}", tags=["Admin"])
async def export_users_to_file(author_id: int):
    result = await export_author_to_file(author_id)
    return result
