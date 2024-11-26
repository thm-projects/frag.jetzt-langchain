

from uuid import UUID
from fastapi import APIRouter, Body, HTTPException, Request

from app.ai_conversation.room_settings.models import InputAPIVoucher, InputRoomAISetting
from app.ai_conversation.room_settings.service import claim_voucher, create_setting, create_voucher, delete_voucher, get_setting, list_voucher, patch_setting, revoke_voucher
from app.security.oauth2 import DEPENDENCIES, ROOM_DEPENDENCIES, per_req_config_modifier


router = APIRouter()

# Room Setting


@router.get("/", dependencies=ROOM_DEPENDENCIES, tags=["Room Setting"])
async def get_room_setting(request: Request):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await get_setting(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", dependencies=ROOM_DEPENDENCIES, tags=["Room Setting"])
async def create_room_setting(request: Request, setting: InputRoomAISetting = Body(..., embed=True)):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await create_setting(config, setting)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/", dependencies=ROOM_DEPENDENCIES, tags=["Room Setting"])
async def patch_room_setting(request: Request, setting: dict = Body(..., embed=True)):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await patch_setting(config, setting)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Voucher

@router.get("/voucher", dependencies=DEPENDENCIES, tags=["Voucher"])
async def list_api_voucher(request: Request):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_voucher(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voucher", dependencies=DEPENDENCIES, tags=["Voucher"])
async def create_api_voucher(request: Request, voucher: InputAPIVoucher = Body(..., embed=True)):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await create_voucher(config, voucher)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/voucher/{id}", dependencies=DEPENDENCIES, tags=["Voucher"])
async def delete_api_voucher(request: Request, id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_voucher(config, id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voucher/claim", dependencies=ROOM_DEPENDENCIES, tags=["Voucher"])
async def claim_api_voucher(request: Request, voucher: str = Body(..., embed=True)):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await claim_voucher(config, voucher)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/voucher/revoke/{id}", dependencies=ROOM_DEPENDENCIES, tags=["Voucher"])
async def revoke_api_voucher(request: Request, id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await revoke_voucher(config, id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))