from typing import List
from uuid import UUID
from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import FileResponse

from app.ai_conversation.file_handling.file_upload import (
    handle_file_upload,
    handle_file_delete,
    handle_file_get,
)
from app.security.oauth2 import DEPENDENCIES

router = APIRouter()


@router.post("/upload", dependencies=DEPENDENCIES)
async def upload(request: Request, files: List[UploadFile] = File(...)) -> list[dict]:
    user_id = "af7c1fe6-d669-414e-b066-e9733f0de7a8"  # request.state.user_id
    return await handle_file_upload(files, user_id)


@router.delete("/delete/{file_id}", dependencies=DEPENDENCIES)
async def delete(request: Request, file_id: UUID) -> None:
    user_id = "af7c1fe6-d669-414e-b066-e9733f0de7a8"  # request.state.user_id
    return await handle_file_delete(file_id, user_id)


@router.get("/content/{file_id}", dependencies=DEPENDENCIES)
async def get_content(request: Request, file_id: UUID) -> FileResponse:
    user_id = "af7c1fe6-d669-414e-b066-e9733f0de7a8" # request.state.user_id
    return await handle_file_get(file_id, user_id)
