from typing import List
from uuid import UUID
from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import FileResponse

from app.ai_conversation.file_handling.file_upload import (
    handle_file_upload,
    handle_file_delete,
    handle_file_get,
    handle_file_list,
)
from app.security.oauth2 import DEPENDENCIES

router = APIRouter()


@router.get("/list", dependencies=DEPENDENCIES, tags=["File"])
async def list_files(request: Request) -> list[dict]:
    return await handle_file_list(request.state.user_id)


@router.post("/upload", dependencies=DEPENDENCIES, tags=["File"])
async def upload(request: Request, files: List[UploadFile] = File(...)) -> list[dict]:
    return await handle_file_upload(files, request.state.user_id)


@router.delete("/delete/{file_id}", dependencies=DEPENDENCIES, tags=["File"])
async def delete(request: Request, file_id: UUID) -> None:
    return await handle_file_delete(file_id, request.state.user_id)


@router.get("/content/{file_id}", dependencies=DEPENDENCIES, tags=["File"])
async def get_content(request: Request, file_id: UUID) -> FileResponse:
    return await handle_file_get(file_id, request.state.user_id)
