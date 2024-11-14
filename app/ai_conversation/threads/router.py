from uuid import UUID
from fastapi import APIRouter, Body, HTTPException, Request
from langchain_core.messages import HumanMessage
from app.ai_conversation.threads.graph import get_graph_wrapper
from sse_starlette.sse import EventSourceResponse

from app.security.oauth2 import DEPENDENCIES, per_req_config_modifier


router = APIRouter()


async def _async_yield_wrapper(generator):
    try:
        async for item in generator:
            yield item
    except Exception as e:
        yield {"event": "error", "data": str(e)}


@router.post("/list", dependencies=DEPENDENCIES)
async def list_chats(request: Request, config: dict = Body(None, embed=True)):
    try:
        config = {"configurable": config.get("configurable", {}) if config else {}}
        await per_req_config_modifier(config, request)
        return await get_graph_wrapper().list_chats(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/new", dependencies=DEPENDENCIES)
async def create_new_chat(
    request: Request, message: HumanMessage = Body(...), config: dict = Body(...)
):
    try:
        config = {"configurable": config.get("configurable", {}) if config else {}}
        await per_req_config_modifier(config, request)
        return EventSourceResponse(
            _async_yield_wrapper(get_graph_wrapper().new_chat(message, config))
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/continue/{thread_id}", dependencies=DEPENDENCIES)
async def continue_chat(
    request: Request,
    thread_id: UUID,
    message: HumanMessage = Body(None),
    config: dict = Body(...),
):
    try:
        config = {"configurable": config.get("configurable", {}) if config else {}}
        await per_req_config_modifier(config, request)
        return EventSourceResponse(
            _async_yield_wrapper(
                get_graph_wrapper().continue_chat(message, thread_id, config)
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{thread_id}", dependencies=DEPENDENCIES)
async def get_chat_messages(request: Request, thread_id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await get_graph_wrapper().get_chat_messages(thread_id, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
