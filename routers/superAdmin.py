from typing import List

from fastapi import APIRouter

from controllers.superAdmin import createUser, readUsers, readUser, updateUser, deleteUser, createRole, createPrivilege
from models.superAdmin import UserCreate, UserRoleCreate, UserPrivilegeCreate

router = APIRouter()


@router.post("/users/", tags=["SuperAdmin"])
async def create_user(user: UserCreate):
    result = await createUser(user)
    return result


@router.get("/users/", tags=["SuperAdmin"])
async def read_users():
    result = await readUsers()
    return result


@router.get("/users/{user_id}", tags=["SuperAdmin"])
async def read_user(user_id: int):
    result = await readUser(user_id)
    return result


@router.put("/users/{user_id}", tags=["SuperAdmin"])
async def update_user(user_id: int, user: UserCreate):
    result = await updateUser(user_id, user)
    return result


@router.delete("/users/{user_id}", tags=["SuperAdmin"])
async def delete_user(user_id: int):
    result = await deleteUser(user_id)
    return result


@router.post("/roles/", tags=["SuperAdmin"])
async def create_role(role: UserRoleCreate):
    result = await createRole(role)
    return result


@router.post("/privileges/", tags=["SuperAdmin"])
async def create_privilege(privilege: UserPrivilegeCreate):
    result = await createPrivilege(privilege)
    return result
