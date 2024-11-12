from typing import Iterable
from uuid import UUID, uuid4
import magic
import os
import imageio
from PIL import Image
from app.ai_conversation.db import load_file
from app.ai_conversation.entities.uploaded_file_content import UploadedFileContent
from app.ai_conversation.file_handling.vectorstore import on_content_deleted
from more_itertools import chunked
from apscheduler.schedulers.asyncio import AsyncIOScheduler

get_unreferenced_content = load_file("get_unreferenced_content")
get_unoptimized_content = load_file("get_unoptimized_content")

currently_processing = {}


def remove_files(ref_list: Iterable[UUID]) -> None:
    for ref in ref_list:
        try:
            os.remove(f"{os.getcwd()}/files/{ref}")
        except FileNotFoundError:
            pass


async def optimize_file_content(
    async_connection_pool, apscheduler: AsyncIOScheduler
) -> None:
    async with async_connection_pool.acquire() as conn:
        to_optimize_files = await conn.fetch(
            get_unoptimized_content, currently_processing.keys()
        )
    if to_optimize_files:
        print(f"Optimizing {len(to_optimize_files)} files")
    for file in to_optimize_files:
        await _add_optimize_job(file, apscheduler, async_connection_pool)


async def _add_optimize_job(
    file: dict, apscheduler: AsyncIOScheduler, async_connection_pool
) -> None:
    if file["file_ref"] not in currently_processing:
        currently_processing[file["file_ref"]] = {"vector": False, "optimize": True}
    apscheduler.add_job(
        _process_file,
        "date",
        args=[UploadedFileContent.load_from_db(file), async_connection_pool],
        id=str(file.file_ref),
    )


async def remove_unreferenced_content(async_connection_pool):
    to_delete_files = []
    async with async_connection_pool.acquire() as conn:
        async with conn.transaction():
            to_delete_files = await conn.fetch(
                get_unreferenced_content, currently_processing.keys()
            )
            if to_delete_files:
                print(f"Deleting {len(to_delete_files)} file contents")
            for to_delete in chunked(to_delete_files, 1000):
                await conn.execute(
                    "DELETE FROM uploaded_file_content WHERE id IN (SELECT unnest($1::uuid[]));",
                    map(lambda x: x["id"], to_delete),
                )

    # notify vetorstore of deletions
    await on_content_deleted(list(map(lambda x: x["id"], to_delete_files)))
    # delete remaining files from fs
    remove_files(map(lambda x: x["file_ref"], to_delete_files))


async def sync_with_db(async_connection_pool):
    files = get_all_files()
    to_delete_db = []
    async with async_connection_pool.acquire() as conn:
        async with conn.transaction():
            async for record in conn.cursor(
                "SELECT id, file_ref FROM uploaded_file_content WHERE id NOT IN (SELECT unnest($1::uuid[]));",
                currently_processing.keys(),
                prefetch=1000,
            ):
                # if file is deleted from fs, delete from db
                if record["file_ref"] not in files:
                    to_delete_db.append(record["id"])
                else:
                    # remove from set, remaining files will be deleted from fs
                    files.discard(record["file_ref"])

            for to_delete in chunked(to_delete_db, 1000):
                await conn.execute(
                    "DELETE FROM uploaded_file_content WHERE id IN $1;", to_delete
                )

    # notify vetorstore of deletions
    await on_content_deleted(to_delete_db)
    # delete remaining files from fs
    remove_files(map(lambda x: x["file_ref"], files))


def get_all_files() -> set[UUID]:
    files = set()
    dir = f"{os.getcwd()}/files"
    for f in os.listdir(dir):
        if not os.path.isfile(f"{dir}/f"):
            continue
        try:
            files.add(UUID(f))
        except ValueError:
            continue
    return files


def generate_file_path() -> tuple[str, UUID]:
    while True:
        uuid = uuid4()
        path = f"{os.getcwd()}/files/{uuid}"
        if not os.path.isfile(path):
            return path, uuid


async def finish_processing(file_ref: UUID) -> None:
    obj = currently_processing[file_ref]
    if obj["vector"] or obj["optimize"]:
        return
    del currently_processing[file_ref]


async def _process_file(file: UploadedFileContent, async_connection_pool) -> None:
    path = f"{os.getcwd()}/files/{file.file_ref}"
    type = magic.from_file(path, mime=True)
    uuid = file.file_ref
    match type:
        case "image/gif":
            uuid = _gif_to_webp(path)
        case "image/jpeg", "image/png":
            uuid = _img_to_webp(path)
        case "application/zip":
            # what to do with zip files? -> extract and process each file
            pass
        case _:
            pass

    async with async_connection_pool.acquire() as conn:
        status = await conn.execute(
            "UPDATE uploaded_file_content SET file_ref = $1, unprocessed = false WHERE id = $2;",
            uuid,
            file.id,
        )
        if status != "UPDATE 1":
            raise Exception("Failed to update file_ref")
    if uuid != file.file_ref:
        os.remove(path)
    currently_processing[file.file_ref]["optimize"] = False
    await finish_processing(file.file_ref)


def _img_to_webp(input_path: str) -> UUID:
    output_path, uuid = generate_file_path()
    img = Image.open(input_path)
    img.save(output_path, "WEBP", optimize=True, quality=80)
    return output_path, uuid


def _gif_to_webp(input_path: str) -> UUID:
    output_path, uuid = generate_file_path()
    gif = Image.open(input_path)
    # 0 means loop forever
    loop_count = gif.info.get("loop", 0)
    # extract durations from frames
    durations = []
    while True:
        # default is 100ms
        duration = gif.info.get("duration", 100)
        durations.append(duration)
        try:
            gif.seek(gif.tell() + 1)
        except EOFError:
            break

    # Read the animated GIF frames using imageio
    gif_frames = imageio.mimread(input_path)
    frames = [Image.fromarray(frame) for frame in gif_frames]
    frames[0].save(
        output_path,
        format="WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=loop_count,
        optimize=True,
        quality=80,
    )
    return output_path, uuid
