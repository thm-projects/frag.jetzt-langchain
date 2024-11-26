from uuid import UUID
from fastapi import APIRouter, Body, HTTPException, Request

from app.ai_conversation.restrictions.models import (
    InputBlockRestriction,
    InputQuotaRestriction,
    InputRestrictions,
    InputTimeRestriction,
)
from app.ai_conversation.restrictions.service import (
    add_block_restriction,
    add_quota_restriction,
    add_time_restriction,
    create_restrictions,
    delete_block_restriction,
    delete_quota_restriction,
    delete_restrictions,
    delete_time_restriction,
    list_block_restrictions,
    list_quota_restrictions,
    list_restrictions,
    list_time_restrictions,
    patch_quota_restriction,
    patch_time_restriction,
)
from app.security.oauth2 import DEPENDENCIES, ROOM_DEPENDENCIES, per_req_config_modifier


router = APIRouter()

# Restrictions Object


@router.get("/", dependencies=DEPENDENCIES, tags=["Restrictions (User)"])
async def get_restrictions(request: Request):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_restrictions(config, False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", dependencies=DEPENDENCIES, tags=["Restrictions (User)"])
async def create_restriction_object(
    request: Request, restriction: InputRestrictions = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await create_restrictions(config, restriction, False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{restrictions_id}", dependencies=DEPENDENCIES, tags=["Restrictions (User)"]
)
async def delete_restriction_object(request: Request, restrictions_id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_restrictions(config, restrictions_id, False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/room/", dependencies=ROOM_DEPENDENCIES, tags=["Restrictions (Room)"])
async def get_room_restrictions(request: Request):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_restrictions(config, True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/room/", dependencies=ROOM_DEPENDENCIES, tags=["Restrictions (Room)"])
async def create_room_restriction_object(
    request: Request, restriction: InputRestrictions = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await create_restrictions(config, restriction, True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/room/{restrictions_id}",
    dependencies=ROOM_DEPENDENCIES,
    tags=["Restrictions (Room)"],
)
async def delete_room_restriction_object(request: Request, restrictions_id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_restrictions(config, restrictions_id, True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Block Restriction


@router.get(
    "/{restrictions_id}/block",
    dependencies=DEPENDENCIES,
    tags=["Restrictions (User) - Block"],
)
async def get_block_restrictions(request: Request, restrictions_id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_block_restrictions(config, restrictions_id, False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/block", dependencies=DEPENDENCIES, tags=["Restrictions (User) - Block"])
async def create_block_restriction(
    request: Request, block_restriction: InputBlockRestriction = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await add_block_restriction(config, block_restriction, False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{restrictions_id}/block/{block_id}",
    dependencies=DEPENDENCIES,
    tags=["Restrictions (User) - Block"],
)
async def remove_block_restriction(
    request: Request, restrictions_id: UUID, block_id: UUID
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_block_restriction(config, restrictions_id, block_id, False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/room/{restrictions_id}/block",
    dependencies=ROOM_DEPENDENCIES,
    tags=["Restrictions (Room) - Block"],
)
async def get_room_block_restrictions(request: Request, restrictions_id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_block_restrictions(config, restrictions_id, True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/room/block", dependencies=ROOM_DEPENDENCIES, tags=["Restrictions (Room) - Block"]
)
async def create_room_block_restriction(
    request: Request, block_restriction: InputBlockRestriction = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await add_block_restriction(config, block_restriction, True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/room/{restrictions_id}/block/{block_id}",
    dependencies=ROOM_DEPENDENCIES,
    tags=["Restrictions (Room) - Block"],
)
async def remove_room_block_restriction(
    request: Request, restrictions_id: UUID, block_id: UUID
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_block_restriction(config, restrictions_id, block_id, True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Quota Restriction


@router.get(
    "/{restrictions_id}/quota",
    dependencies=DEPENDENCIES,
    tags=["Restrictions (User) - Quota"],
)
async def get_quota_restrictions(request: Request, restrictions_id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_quota_restrictions(config, restrictions_id, False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quota", dependencies=DEPENDENCIES, tags=["Restrictions (User) - Quota"])
async def create_quota_restriction(
    request: Request, quota_restriction: InputQuotaRestriction = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await add_quota_restriction(config, quota_restriction, False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/{restrictions_id}/quota/{quota_id}",
    dependencies=DEPENDENCIES,
    tags=["Restrictions (User) - Quota"],
)
async def update_quota_restriction(
    request: Request,
    restrictions_id: UUID,
    quota_id: UUID,
    patch: dict = Body(..., embed=True),
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await patch_quota_restriction(
            config, restrictions_id, quota_id, patch, False
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{restrictions_id}/quota/{quota_id}",
    dependencies=DEPENDENCIES,
    tags=["Restrictions (User) - Quota"],
)
async def remove_quota_restriction(
    request: Request, restrictions_id: UUID, quota_id: UUID
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_quota_restriction(config, restrictions_id, quota_id, False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/room/{restrictions_id}/quota",
    dependencies=ROOM_DEPENDENCIES,
    tags=["Restrictions (Room) - Quota"],
)
async def get_room_quota_restrictions(request: Request, restrictions_id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_quota_restrictions(config, restrictions_id, True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/room/quota", dependencies=ROOM_DEPENDENCIES, tags=["Restrictions (Room) - Quota"]
)
async def create_room_quota_restriction(
    request: Request, quota_restriction: InputQuotaRestriction = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await add_quota_restriction(config, quota_restriction, True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/room/{restrictions_id}/quota/{quota_id}",
    dependencies=ROOM_DEPENDENCIES,
    tags=["Restrictions (Room) - Quota"],
)
async def update_room_quota_restriction(
    request: Request,
    restrictions_id: UUID,
    quota_id: UUID,
    patch: dict = Body(..., embed=True),
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await patch_quota_restriction(
            config, restrictions_id, quota_id, patch, True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/room/{restrictions_id}/quota/{quota_id}",
    dependencies=ROOM_DEPENDENCIES,
    tags=["Restrictions (Room) - Quota"],
)
async def remove_room_quota_restriction(
    request: Request, restrictions_id: UUID, quota_id: UUID
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_quota_restriction(config, restrictions_id, quota_id, True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Time Restrictions


@router.get(
    "/{restrictions_id}/time",
    dependencies=DEPENDENCIES,
    tags=["Restrictions (User) - Time"],
)
async def get_time_restrictions(request: Request, restrictions_id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_time_restrictions(config, restrictions_id, False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/time", dependencies=DEPENDENCIES, tags=["Restrictions (User) - Time"])
async def create_time_restriction(
    request: Request, time_restriction: InputTimeRestriction = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await add_time_restriction(config, time_restriction, False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/{restrictions_id}/time/{time_id}",
    dependencies=DEPENDENCIES,
    tags=["Restrictions (User) - Time"],
)
async def update_time_restriction(
    request: Request,
    restrictions_id: UUID,
    time_id: UUID,
    patch: dict = Body(..., embed=True),
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await patch_time_restriction(
            config, restrictions_id, time_id, patch, False
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{restrictions_id}/time/{time_id}",
    dependencies=DEPENDENCIES,
    tags=["Restrictions (User) - Time"],
)
async def remove_time_restriction(
    request: Request, restrictions_id: UUID, time_id: UUID
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_time_restriction(config, restrictions_id, time_id, False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/room/{restrictions_id}/time",
    dependencies=ROOM_DEPENDENCIES,
    tags=["Restrictions (Room) - Time"],
)
async def get_room_time_restrictions(request: Request, restrictions_id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_time_restrictions(config, restrictions_id, True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/room/time", dependencies=ROOM_DEPENDENCIES, tags=["Restrictions (Room) - Time"]
)
async def create_room_time_restriction(
    request: Request, time_restriction: InputTimeRestriction = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await add_time_restriction(config, time_restriction, True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/room/{restrictions_id}/time/{time_id}",
    dependencies=ROOM_DEPENDENCIES,
    tags=["Restrictions (Room) - Time"],
)
async def update_room_time_restriction(
    request: Request,
    restrictions_id: UUID,
    time_id: UUID,
    patch: dict = Body(..., embed=True),
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await patch_time_restriction(
            config, restrictions_id, time_id, patch, True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/room/{restrictions_id}/time/{time_id}",
    dependencies=ROOM_DEPENDENCIES,
    tags=["Restrictions (Room) - Time"],
)
async def remove_room_time_restriction(
    request: Request, restrictions_id: UUID, time_id: UUID
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_time_restriction(config, restrictions_id, time_id, True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
