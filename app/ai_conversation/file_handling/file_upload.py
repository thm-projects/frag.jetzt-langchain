import os
import shutil
from typing import List
from uuid import UUID
from fastapi import HTTPException, UploadFile
import aiofiles
from hashlib import sha256
import base64

from fastapi.responses import FileResponse
import magic
from app.ai_conversation.db import load_file
from app.ai_conversation.ai_conversation import get_connection_pool, get_scheduler
from app.ai_conversation.entities.uploaded_file_content import UploadedFileContent
from app.ai_conversation.file_handling.file_upload_processor import (
    generate_file_path,
    remove_files,
    currently_processing,
    _add_optimize_job,
)
from app.ai_conversation.file_handling.vectorstore import import_to_vectorstore

create_content = load_file("create_content")
create_file = load_file("create_file")


async def handle_file_upload(files: List[UploadFile], user_id: UUID) -> list[dict]:
    results = []
    for file in files:
        result = await _handle_file(file)
        if isinstance(result, str):
            results.append(
                {"result": "Failed", "reason": result, "filename": file.filename}
            )
            continue
        hash, file_ref = result
        row = await _find_content_by_hash(hash, file_ref)
        is_new = row["file_ref"] == file_ref
        import_result = None
        if is_new:
            currently_processing[file_ref] = {"vector": True, "optimize": True}
            # first extract for vector
            try:
                import_result = await import_to_vectorstore(
                    UploadedFileContent.load_from_db(row)
                )
            except Exception as e:
                import_result = "Failed"
                print(e)
            currently_processing[file_ref]["vector"] = False
            # then optimize
            await _add_optimize_job(row, get_scheduler(), get_connection_pool())
        else:
            remove_files([file_ref])
        file = await _insert_file(row["id"], user_id, file.filename)
        results.append(
            {
                "result": "OK",
                "file": dict(file),
                "isNew": is_new,
                "importResult": import_result,
            }
        )
    return results

async def handle_file_list(user_id: UUID):
    async with get_connection_pool().acquire() as conn:
        files = await conn.fetch(
            "SELECT * FROM uploaded_file WHERE account_id = $1;",
            user_id,
        )
        return [dict(file) for file in files]


async def handle_file_delete(file_id: UUID, user_id: UUID):
    async with get_connection_pool().acquire() as conn:
        status = await conn.execute(
            "DELETE FROM uploaded_file WHERE id = $1 and account_id = $2;",
            file_id,
            user_id,
        )
        if status != "DELETE 1":
            raise HTTPException(status_code=404, detail="File not found")
        return None


async def handle_file_get(file_id: str, user_id: UUID):
    async with get_connection_pool().acquire() as conn:
        file = await conn.fetchrow(
            "SELECT * FROM uploaded_file WHERE id = $1 and account_id = $2;",
            file_id,
            user_id,
        )
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        path = f"{os.getcwd()}/files/{file['file_ref']}"
        media_type = magic.from_file(path, mime=True)
        return FileResponse(path=path, filename=file["name"], media_type=media_type)


async def _find_content_by_hash(hash: str, file_ref: str, unprocessed: bool = True):
    async with get_connection_pool().acquire() as conn:
        return await conn.fetchrow(create_content, hash, file_ref, unprocessed)


async def _insert_file(content_id: UUID, account_id: UUID, name: str):
    async with get_connection_pool().acquire() as conn:
        return await conn.fetchrow(
            create_file,
            content_id,
            account_id,
            name,
        )


def _get_remaining_fs_size():
    os.makedirs(f"{os.getcwd()}/files", exist_ok=True)
    _, _, free = shutil.disk_usage(f"{os.getcwd()}/files")
    return free


async def _handle_file(file: UploadFile):
    destination, file_ref = generate_file_path()
    hash = sha256()
    first_bytes = None
    last_bytes = None
    file_size = file.file.seek(0, 2)
    file.file.seek(0)
    if file_size > _get_remaining_fs_size() * 3 / 4:
        return "Not enough space"
    async with aiofiles.open(destination, "wb") as out_file:
        # async read file chunk
        while content := await file.read(4096):
            # Compute for identifying file
            if not first_bytes:
                first_bytes = content[:16]
            last_bytes = content
            hash.update(content)
            # async write file chunk
            await out_file.write(content)
    if last_bytes is None:
        return "File is empty"
    # create identifying hash
    last_bytes = last_bytes[-16:]
    identifier = base64.b64encode(hash.digest() + first_bytes + last_bytes).decode()
    return identifier, file_ref
