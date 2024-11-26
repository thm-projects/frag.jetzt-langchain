from uuid import UUID
from fastapi import APIRouter, Body, HTTPException, Request

from app.ai_conversation.assistants.models import (
    InputAssistant,
    OutputAssistant,
    WrappedAssistant,
)
from app.ai_conversation.assistants.service import (
    list_user_assistants,
    create_user_assistant as c_u_assistant,
    delete_user_assistant as d_u_assistant,
    patch_user_assistant as p_u_assistant,
    get_user_assistant_files as file_u_get,
    add_user_assistant_files as file_u_add,
    delete_user_assistant_file as file_u_delete,
    list_room_assistants,
    create_room_assistant as c_r_assistant,
    delete_room_assistant as d_r_assistant,
    patch_room_assistant as p_r_assistant,
    get_room_assistant_files as file_r_get,
    add_room_assistant_files as file_r_add,
    delete_room_assistant_file as file_r_delete,
    list_platform_assistant,
    create_platform_assistant as c_p_assistant,
    delete_platform_assistant as d_p_assistant,
    patch_platform_assistant as p_p_assistant,
    get_platform_assistant_files as file_p_get,
    add_platform_assistant_files as file_p_add,
    delete_platform_assistant_file as file_p_delete,
)
from app.security.oauth2 import DEPENDENCIES, ROOM_DEPENDENCIES, per_req_config_modifier


router = APIRouter()


@router.get("/assistant", dependencies=DEPENDENCIES, tags=["Assistant (User)"])
async def get_user_assistants(request: Request) -> list[WrappedAssistant]:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_user_assistants(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assistant", dependencies=DEPENDENCIES, tags=["Assistant (User)"])
async def create_user_assistant(
    request: Request, assistant: InputAssistant = Body(..., embed=True)
) -> OutputAssistant:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await c_u_assistant(config, assistant)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/assistant/{assistant_id}", dependencies=DEPENDENCIES, tags=["Assistant (User)"]
)
async def delete_user_assistant(request: Request, assistant_id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await d_u_assistant(config, assistant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/assistant/{assistant_id}", dependencies=DEPENDENCIES, tags=["Assistant (User)"]
)
async def patch_user_assistant(
    request: Request, assistant_id: UUID, assistant: dict = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await p_u_assistant(config, assistant_id, assistant)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/assistant/{assistant_id}/file",
    dependencies=DEPENDENCIES,
    tags=["Assistant (User) - Files"],
)
async def get_user_assistant_files(request: Request, assistant_id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await file_u_get(config, assistant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/assistant/{assistant_id}/file",
    dependencies=DEPENDENCIES,
    tags=["Assistant (User) - Files"],
)
async def add_user_assistant_files(
    request: Request, assistant_id: UUID, files: list[UUID] = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await file_u_add(config, assistant_id, files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/assistant/{assistant_id}/file/delete-request",
    dependencies=DEPENDENCIES,
    tags=["Assistant (User) - Files"],
)
async def delete_user_assistant_file(
    request: Request, assistant_id: UUID, file_ids: list[UUID] = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await file_u_delete(config, assistant_id, file_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/room-assistant", dependencies=ROOM_DEPENDENCIES, tags=["Assistant (Room)"]
)
async def get_room_assistants(request: Request) -> list[WrappedAssistant]:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_room_assistants(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/room-assistant", dependencies=ROOM_DEPENDENCIES, tags=["Assistant (Room)"]
)
async def create_room_assistant(
    request: Request, assistant: InputAssistant = Body(..., embed=True)
) -> OutputAssistant:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await c_r_assistant(config, assistant)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/room-assistant/{assistant_id}",
    dependencies=ROOM_DEPENDENCIES,
    tags=["Assistant (Room)"],
)
async def delete_room_assistant(request: Request, assistant_id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await d_r_assistant(config, assistant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/room-assistant/{assistant_id}",
    dependencies=ROOM_DEPENDENCIES,
    tags=["Assistant (Room)"],
)
async def patch_room_assistant(
    request: Request, assistant_id: UUID, assistant: dict = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await p_r_assistant(config, assistant_id, assistant)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/room-assistant/{assistant_id}/file",
    dependencies=ROOM_DEPENDENCIES,
    tags=["Assistant (Room) - Files"],
)
async def get_room_assistant_files(request: Request, assistant_id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await file_r_get(config, assistant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/room-assistant/{assistant_id}/file",
    dependencies=ROOM_DEPENDENCIES,
    tags=["Assistant (Room) - Files"],
)
async def add_room_assistant_files(
    request: Request, assistant_id: UUID, files: list[UUID] = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await file_r_add(config, assistant_id, files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/room-assistant/{assistant_id}/file/delete-request",
    dependencies=ROOM_DEPENDENCIES,
    tags=["Assistant (Room) - Files"],
)
async def delete_room_assistant_file(
    request: Request, assistant_id: UUID, file_ids: list[UUID] = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await file_r_delete(config, assistant_id, file_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/platform-assistant", dependencies=DEPENDENCIES, tags=["Assistant (Platform)"]
)
async def get_platform_assistants(request: Request) -> list[WrappedAssistant]:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_platform_assistant(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/platform-assistant", dependencies=DEPENDENCIES, tags=["Assistant (Platform)"]
)
async def create_platform_assistant(
    request: Request, assistant: InputAssistant = Body(..., embed=True)
) -> OutputAssistant:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await c_p_assistant(config, assistant)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/platform-assistant/{assistant_id}",
    dependencies=DEPENDENCIES,
    tags=["Assistant (Platform)"],
)
async def delete_platform_assistant(request: Request, assistant_id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await d_p_assistant(config, assistant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/platform-assistant/{assistant_id}",
    dependencies=DEPENDENCIES,
    tags=["Assistant (Platform)"],
)
async def patch_platform_assistant(
    request: Request, assistant_id: UUID, assistant: dict = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await p_p_assistant(config, assistant_id, assistant)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/platform-assistant/{assistant_id}/file",
    dependencies=DEPENDENCIES,
    tags=["Assistant (Platform) - Files"],
)
async def get_platform_assistant_files(request: Request, assistant_id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await file_p_get(config, assistant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/platform-assistant/{assistant_id}/file",
    dependencies=DEPENDENCIES,
    tags=["Assistant (Platform) - Files"],
)
async def add_platform_assistant_files(
    request: Request, assistant_id: UUID, files: list[UUID] = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await file_p_add(config, assistant_id, files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/platform-assistant/{assistant_id}/file/delete-request",
    dependencies=DEPENDENCIES,
    tags=["Assistant (Platform) - Files"],
)
async def delete_platform_assistant_file(
    request: Request, assistant_id: UUID, file_ids: list[UUID] = Body(..., embed=True)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await file_p_delete(config, assistant_id, file_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
