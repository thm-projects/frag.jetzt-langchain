from uuid import UUID
from app.ai_conversation.ai_conversation import get_connection_pool
from app.ai_conversation.room_settings.models import (
    APIVoucher,
    InputAPIVoucher,
    InputRoomAISetting,
    RoomAISetting,
)
from app.ai_conversation.services.role_checker import AdminRole, Role


async def create_setting(config: dict, setting: InputRoomAISetting) -> RoomAISetting:
    room_id = config["configurable"]["room"]["id"]
    role = config["configurable"]["role"]
    if role not in [Role.CREATOR, Role.MODERATOR]:
        raise ValueError("You must be at least Moderator!")
    if setting.room_id != room_id:
        raise ValueError("Room Ids do not match")
    async with get_connection_pool().acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO room_ai_setting(room_id, restriction_id, api_setup_id, allow_global_assistants, allow_user_assistants) VALUES ($1, $2, $3, $4, $5) RETURNING *;",
            setting.room_id,
            setting.restriction_id,
            setting.api_setup_id,
            setting.allow_global_assistants,
            setting.allow_user_assistants,
        )
        return RoomAISetting.load_from_db(row)


async def patch_setting(config: dict, setting: dict) -> RoomAISetting:
    room_id = config["configurable"]["room"]["id"]
    role = config["configurable"]["role"]
    if role not in [Role.CREATOR, Role.MODERATOR]:
        raise ValueError("You must be at least Moderator!")
    async with get_connection_pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM room_ai_setting WHERE room_id = $1;", room_id
        )
        if not row:
            raise ValueError("Setting does not exist")
        if "restriction_id" in setting:
            row["restriction_id"] = setting["restriction_id"]
        if "api_setup_id" in setting:
            row["api_setup_id"] = setting["api_setup_id"]
        if "allow_global_assistants":
            row["allow_global_assistants"] = setting["allow_global_assistants"]
        if "allow_user_assistants":
            row["allow_user_assistants"] = setting["allow_user_assistants"]
        row = await conn.fetchrow(
            "UPDATE room_ai_setting SET restriction_id = $1, api_setup_id = $2, allow_global_assistants = $3, allow_user_assistants = $4 WHERE id = $5 RETURNING *;",
            row["restriction_id"],
            row["api_setup_id"],
            row["allow_global_assistants"],
            row["allow_user_assistants"],
            row["id"],
        )
        return RoomAISetting.load_from_db(row)


async def get_setting(config: dict) -> RoomAISetting:
    room_id = config["configurable"]["room"]["id"]
    async with get_connection_pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM room_ai_setting WHERE room_id = $1;", room_id
        )
        if not row:
            raise ValueError("Not found")
        return RoomAISetting.load_from_db(row)


async def create_voucher(config: dict, voucher: InputAPIVoucher) -> APIVoucher:
    roles = config["configurable"]["user_info"]["admin_roles"]
    can_use = AdminRole.ADMIN_DASHBORAD in roles
    if not can_use:
        raise ValueError("You must be at least Admin!")
    async with get_connection_pool().acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO api_voucher(voucher, restriction_id) VALUES ($1, $2) RETURNING *;",
            voucher.voucher,
            voucher.restriction_id,
        )
        return APIVoucher.load_from_db(row)


async def revoke_voucher(config: dict, voucher_id: InputAPIVoucher) -> dict:
    roles = config["configurable"]["user_info"]["admin_roles"]
    room_id = config["configurable"]["room"]["id"]
    role = config["configurable"]["role"]
    can_use = AdminRole.ADMIN_DASHBORAD in roles or role not in [
        Role.CREATOR,
        Role.MODERATOR,
    ]
    if not can_use:
        raise ValueError("You are not allowed to revoke the voucher!")
    async with get_connection_pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT room_id FROM api_voucher WHERE id = $1", voucher_id
        )
        if not row:
            raise ValueError("Voucher not present")
        if not row["room_id"]:
            raise ValueError("Voucher not taken")
        if room_id != row["room_id"]:
            raise ValueError("Room Ids are not matching")
        await conn.execute(
            "UPDATE room_ai_setting SET api_voucher_id = NULL WHERE id = $1;", room_id
        )
        await conn.execute(
            "UPDATE api_voucher SET room_id = NULL WHERE id = $1;", voucher_id
        )
        return {"status": "OK"}


async def delete_voucher(config: dict, voucher_id: UUID):
    roles = config["configurable"]["user_info"]["admin_roles"]
    can_use = AdminRole.ADMIN_DASHBORAD in roles
    if not can_use:
        raise ValueError("You must be at least Admin!")
    async with get_connection_pool().acquire() as conn:
        status = await conn.execute(
            "DELETE FROM api_voucher WHERE id = $1;", voucher_id
        )
        if not status:
            raise ValueError("Voucher does not exist")


async def list_voucher(config: dict) -> list[APIVoucher]:
    roles = config["configurable"]["user_info"]["admin_roles"]
    can_use = AdminRole.ADMIN_DASHBORAD in roles
    if not can_use:
        raise ValueError("You must be at least Admin!")
    async with get_connection_pool().acquire() as conn:
        rows = await conn.fetch("SELECT * FROM api_voucher;")
        rows = rows or []
        return [APIVoucher.load_from_db(row) for row in rows]


async def claim_voucher(config: dict, voucher: str) -> dict:
    roles = config["configurable"]["user_info"]["admin_roles"]
    room_id = config["configurable"]["room"]["id"]
    role = config["configurable"]["role"]
    can_use = AdminRole.ADMIN_DASHBORAD in roles or role not in [
        Role.CREATOR,
        Role.MODERATOR,
    ]
    if not can_use:
        raise ValueError("You must be at least Moderator!")
    async with get_connection_pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM api_voucher WHERE voucher = $1 AND room_id = $2;",
            voucher,
            room_id,
        )
        if not row:
            raise ValueError("No voucher found")
        await conn.execute(
            "UPDATE room_ai_setting SET api_voucher_id = $1 WHERE id = $2;",
            row["id"],
            room_id,
        )
        await conn.execute(
            "UPDATE api_voucher SET room_id = $1 WHERE id = $2;", room_id, row["id"]
        )
        return {"status": "OK"}
