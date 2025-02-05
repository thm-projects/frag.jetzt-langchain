from uuid import UUID

from fastapi import HTTPException
from app.ai_conversation.ai_conversation import get_connection_pool
from app.ai_conversation.entities.thread import Thread


async def list_threads(room_id: UUID, account_id: UUID) -> list[Thread]:
    async with get_connection_pool().acquire() as conn:
        threads = await conn.fetch(
            "SELECT * FROM thread WHERE room_id = $1 AND account_id = $2 ORDER BY created_at DESC;",
            room_id,
            account_id,
        )
        return [Thread.load_from_db(thread) for thread in threads]


async def create_thread(room_id: UUID, account_id: UUID, name: str) -> Thread:
    async with get_connection_pool().acquire() as conn:
        thread = await conn.fetchrow(
            "INSERT INTO thread(room_id, account_id, name) VALUES($1, $2, $3) RETURNING *;",
            room_id,
            account_id,
            name,
        )
        return Thread.load_from_db(thread)


async def get_thread(thread_id: UUID, room_id: UUID | None, account_id: UUID) -> Thread:
    async with get_connection_pool().acquire() as conn:
        if room_id is None:
            thread = await conn.fetchrow(
                "SELECT * FROM thread WHERE id = $1 AND account_id = $2;",
                thread_id,
                account_id,
            )
        else:
            thread = await conn.fetchrow(
                "SELECT * FROM thread WHERE id = $1 AND room_id = $2 AND account_id = $3;",
                thread_id,
                room_id,
                account_id,
            )
        return Thread.load_from_db(thread) if thread else None


async def delete_thread(thread_id: UUID, room_id: UUID | None, account_id: UUID):
    async with get_connection_pool().acquire() as conn:
        if room_id is None:
            thread = await conn.fetchrow(
                "SELECT * FROM thread WHERE id = $1 AND account_id = $2;",
                thread_id,
                account_id,
            )
        else:
            thread = await conn.fetchrow(
                "SELECT * FROM thread WHERE id = $1 AND room_id = $2 AND account_id = $3;",
                thread_id,
                room_id,
                account_id,
            )
        if thread is None:
            raise HTTPException(
                status_code=404,
                detail="Thread not found",
            )
        # First, delete all messages (checkpoints) in the thread
        await conn.execute(
            "DELETE FROM checkpoints WHERE thread_id = $1;",
            str(thread_id),
        )
        await conn.execute(
            "DELETE FROM checkpoint_writes WHERE thread_id = $1;",
            str(thread_id),
        )
        await conn.execute(
            "DELETE FROM checkpoint_blobs WHERE thread_id = $1;",
            str(thread_id),
        )
        # Then delete the thread itself
        await conn.execute(
            "DELETE FROM thread WHERE id = $1 AND account_id = $2;",
            thread_id,
            account_id,
        )
