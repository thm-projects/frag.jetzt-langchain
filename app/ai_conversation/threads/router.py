from uuid import UUID
from fastapi import APIRouter, Body, HTTPException, Request
from langchain_core.messages import HumanMessage
from app.ai_conversation.threads.graph import get_graph_wrapper
from sse_starlette.sse import EventSourceResponse

from app.security.oauth2 import DEPENDENCIES, ROOM_DEPENDENCIES, per_req_config_modifier
import traceback


router = APIRouter()


async def _async_yield_wrapper(generator):
    try:
        async for item in generator:
            yield item
    except Exception as e:
        print(traceback.format_exc())
        yield {"event": "error", "data": str(e)}


@router.get("/list", dependencies=ROOM_DEPENDENCIES, tags=["Thread"])
async def list_chats(request: Request):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await get_graph_wrapper().list_chats(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/new", dependencies=ROOM_DEPENDENCIES, tags=["Thread"])
async def create_new_chat(
    request: Request, message: HumanMessage = Body(...), assistant_id: UUID = Body(...)
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return EventSourceResponse(
            _async_yield_wrapper(
                get_graph_wrapper().new_chat(config, message, assistant_id)
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/continue/{thread_id}", dependencies=ROOM_DEPENDENCIES, tags=["Thread"])
async def continue_chat(
    request: Request,
    thread_id: UUID,
    message: HumanMessage = Body(None),
    assistant_id: UUID = Body(...),
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return EventSourceResponse(
            _async_yield_wrapper(
                get_graph_wrapper().continue_chat(
                    config, thread_id, assistant_id, message
                )
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{thread_id}", dependencies=DEPENDENCIES, tags=["Thread"])
async def get_chat_messages(request: Request, thread_id: UUID):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await get_graph_wrapper().get_chat_messages(thread_id, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
