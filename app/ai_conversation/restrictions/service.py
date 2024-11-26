from uuid import UUID
from app.ai_conversation.ai_conversation import get_connection_pool
from app.ai_conversation.restrictions.models import (
    BlockRestriction,
    InputBlockRestriction,
    InputQuotaRestriction,
    InputRestrictions,
    InputTimeRestriction,
    QuotaRestriction,
    Restrictions,
    TimeRestriction,
)
from app.ai_conversation.services.role_checker import Role
import pytz

from app.ai_conversation.utils import date_to_db


async def create_restrictions(
    config: dict, input: InputRestrictions, room: bool, administrated=False
) -> Restrictions:
    account_id = config["configurable"]["user_info"]["id"]
    if room:
        room_id = config["configurable"]["room"]["id"]
        role = config["configurable"]["role"]
        if role not in [Role.CREATOR, Role.MODERATOR]:
            raise ValueError("You must be at least Moderator!")
        if input.room_id != room_id:
            raise ValueError("You are trying to create restrictions for an other room!")
    else:
        if str(input.account_id) != account_id:
            raise ValueError(
                "You are trying to create restrictions for an other account!"
            )

    async with get_connection_pool().acquire() as conn:
        if room:
            data = await conn.fetchrow(
                "INSERT INTO restrictions(room_id, administrated) VALUES ($1, $2) RETURNING *;",
                room_id,
                administrated,
            )
        else:
            data = await conn.fetchrow(
                "INSERT INTO restrictions(account_id, administrated) VALUES ($1, $2) RETURNING *;",
                account_id,
                administrated,
            )
        if not data:
            raise ValueError("Creation failed")
        return Restrictions.load_from_db(data)


async def list_restrictions(
    config: dict, room: bool, administrated=False
) -> list[Restrictions]:
    account_id = config["configurable"]["user_info"]["id"]
    if room:
        room_id = config["configurable"]["room"]["id"]
        role = config["configurable"]["role"]
        if role not in [Role.CREATOR, Role.MODERATOR]:
            raise ValueError("You must be at least Moderator!")
    async with get_connection_pool().acquire() as conn:
        if room:
            data = await conn.fetch(
                "SELECT * FROM restrictions WHERE room_id = $1 AND administrated = $2;",
                room_id,
                administrated,
            )
        else:
            data = await conn.fetch(
                "SELECT * FROM restrictions WHERE account_id = $1 AND administrated = $2;",
                account_id,
                administrated,
            )
        data = data or []
        return [Restrictions.load_from_db(d) for d in data]


async def delete_restrictions(config: dict, restriction_id: UUID, room: bool):
    async with get_connection_pool().acquire() as conn:
        if room:
            room_id = config["configurable"]["room"]["id"]
            role = config["configurable"]["role"]
            if role not in [Role.CREATOR, Role.MODERATOR]:
                raise ValueError("You must be at least Moderator!")
            status = await conn.execute(
                "DELETE FROM restrictions WHERE room_id = $1 and id = $2;",
                room_id,
                restriction_id,
            )
        else:
            account_id = config["configurable"]["user_info"]["id"]
            status = await conn.execute(
                "DELETE FROM restrictions WHERE account_id = $1 and id = $2;",
                account_id,
                restriction_id,
            )
        return status


async def _check_rights(conn, config: dict, restriction_id: UUID, room: bool) -> None:
    if room:
        room_id = config["configurable"]["room"]["id"]
        role = config["configurable"]["role"]
        if role not in [Role.CREATOR, Role.MODERATOR]:
            raise ValueError("You must be at least Moderator!")
        data = await conn.fetchrow(
            "SELECT id FROM restrictions WHERE room_id = $1 AND id = $2;",
            room_id,
            restriction_id,
        )
    else:
        account_id = config["configurable"]["user_info"]["id"]
        data = await conn.fetchrow(
            "SELECT id FROM restrictions WHERE account_id = $1 AND id = $2;",
            account_id,
            restriction_id,
        )
    if not data:
        raise ValueError("Restriction does not exist")


async def add_block_restriction(
    config: dict, input_restriction: InputBlockRestriction, room: bool
) -> BlockRestriction:
    async with get_connection_pool().acquire() as conn:
        await _check_rights(conn, config, input_restriction.restriction_id, room)
        data = await conn.fetchrow(
            "INSERT INTO block_restriction(restriction_id, target) VALUES ($1, $2) RETURNING *;",
            input_restriction.restriction_id,
            input_restriction.target,
        )
        if not data:
            raise ValueError("Creation failed")
        return BlockRestriction.load_from_db(data)


async def list_block_restrictions(
    config: dict, restriction_id: UUID, room: bool
) -> list[BlockRestriction]:
    async with get_connection_pool().acquire() as conn:
        await _check_rights(conn, config, restriction_id, room)
        data = await conn.fetch(
            "SELECT * FROM block_restriction WHERE restriction_id = $1;",
            restriction_id,
        )
        data = data or []
        return [BlockRestriction.load_from_db(row) for row in data]


async def delete_block_restriction(
    config: dict, restriction_id: UUID, block_restriction_id: UUID, room: bool
):
    async with get_connection_pool().acquire() as conn:
        await _check_rights(conn, config, restriction_id, room)
        status = await conn.execute(
            "DELETE FROM block_restriction WHERE restriction_id = $1 AND id = $2;",
            restriction_id,
            block_restriction_id,
        )
        if not status:
            raise ValueError("Block Restriction not present")


async def add_quota_restriction(
    config: dict, input_restriction: InputQuotaRestriction, room: bool
) -> QuotaRestriction:
    timezone = None
    try:
        timezone = pytz.timezone(input_restriction.timezone)
    except Exception:
        raise ValueError("Timezone is not valid")
    async with get_connection_pool().acquire() as conn:
        await _check_rights(conn, config, input_restriction.restriction_id, room)
        data = await conn.fetchrow(
            "INSERT INTO quota_restriction(restriction_id, quota, target, reset_strategy, timezone, last_reset, end_time) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *;",
            input_restriction.restriction_id,
            input_restriction.quota,
            input_restriction.target,
            input_restriction.reset_strategy,
            input_restriction.timezone,
            date_to_db(input_restriction.last_reset, timezone),
            date_to_db(input_restriction.end_time, timezone),
        )
        if not data:
            raise ValueError("Creation failed")
        return QuotaRestriction.load_from_db(data)


async def list_quota_restrictions(
    config: dict, restriction_id: UUID, room: bool
) -> list[QuotaRestriction]:
    async with get_connection_pool().acquire() as conn:
        await _check_rights(conn, config, restriction_id, room)
        data = await conn.fetch(
            "SELECT * FROM quota_restriction WHERE restriction_id = $1;",
            restriction_id,
        )
        data = data or []
        return [QuotaRestriction.load_from_db(row) for row in data]


async def delete_quota_restriction(
    config: dict, restriction_id: UUID, quota_restriction_id: UUID, room: bool
):
    async with get_connection_pool().acquire() as conn:
        await _check_rights(conn, config, restriction_id, room)
        status = await conn.execute(
            "DELETE FROM quota_restriction WHERE restriction_id = $1 AND id = $2;",
            restriction_id,
            quota_restriction_id,
        )
        if not status:
            raise ValueError("Quota Restriction not present")


async def patch_quota_restriction(
    config: dict,
    restriction_id: UUID,
    quota_restriction_id: UUID,
    quota: dict,
    room: bool,
) -> QuotaRestriction:
    async with get_connection_pool().acquire() as conn:
        await _check_rights(conn, config, restriction_id, room)
        row = await conn.fetchrow(
            "SELECT * FROM quota_restriction WHERE restriction_id = $1 AND id = $2;",
            restriction_id,
            quota_restriction_id,
        )
        if "quota" in quota:
            row["quota"] = quota["quota"]
        if "target" in quota:
            row["target"] = quota["target"]
        if "reset_strategy" in quota:
            row["reset_strategy"] = quota["reset_strategy"]
        if "timezone" in quota:
            row["timezone"] = quota["timezone"]
        if "end_time" in quota:
            row["end_time"] = quota["end_time"]
        if "last_reset" in quota:
            row["last_reset"] = quota["last_reset"]
        timezone = pytz.timezone(row["timezone"])
        row = await conn.fetchrow(
            "UPDATE quota_restriction SET quota = $1, target = $2, reset_strategy = $3, timezone = $4, end_time = $5, last_reset = $6 WHERE restriction_id = $7 AND id = $8 RETURNING *;",
            row["quota"],
            row["target"],
            row["reset_strategy"],
            row["timezone"],
            date_to_db(row["end_time"], timezone),
            date_to_db(row["last_reset"], timezone),
            row["restriction_id"],
            row["id"],
        )
        return QuotaRestriction.load_from_db(row)


async def add_time_restriction(
    config: dict, input_restriction: InputTimeRestriction, room: bool
) -> TimeRestriction:
    timezone = None
    try:
        timezone = pytz.timezone(input_restriction.timezone)
    except Exception:
        raise ValueError("Timezone is not valid")
    async with get_connection_pool().acquire() as conn:
        await _check_rights(conn, config, input_restriction.restriction_id, room)
        data = await conn.fetchrow(
            "INSERT INTO time_restriction(restriction_id, target, repeat_strategy, start_time, end_time, timezone) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *;",
            input_restriction.restriction_id,
            input_restriction.target,
            input_restriction.repeat_strategy,
            date_to_db(input_restriction.start_time, timezone),
            date_to_db(input_restriction.end_time, timezone),
            input_restriction.timezone,
        )
        if not data:
            raise ValueError("Creation failed")
        return TimeRestriction.load_from_db(data)


async def list_time_restrictions(
    config: dict, restriction_id: UUID, room: bool
) -> list[TimeRestriction]:
    async with get_connection_pool().acquire() as conn:
        await _check_rights(conn, config, restriction_id, room)
        data = await conn.fetch(
            "SELECT * FROM time_restriction WHERE restriction_id = $1;",
            restriction_id,
        )
        data = data or []
        return [TimeRestriction.load_from_db(row) for row in data]


async def delete_time_restriction(
    config: dict, restriction_id: UUID, time_restriction_id: UUID, room: bool
):
    async with get_connection_pool().acquire() as conn:
        await _check_rights(conn, config, restriction_id, room)
        status = await conn.execute(
            "DELETE FROM time_restriction WHERE restriction_id = $1 AND id = $2;",
            restriction_id,
            time_restriction_id,
        )
        if not status:
            raise ValueError("Time Restriction not present")


async def patch_time_restriction(
    config: dict,
    restriction_id: UUID,
    time_restriction_id: UUID,
    time_obj: dict,
    room: bool,
) -> TimeRestriction:
    async with get_connection_pool().acquire() as conn:
        await _check_rights(conn, config, restriction_id, room)
        row = await conn.fetchrow(
            "SELECT * FROM time_restriction WHERE restriction_id = $1 AND id = $2;",
            restriction_id,
            time_restriction_id,
        )
        if "start_time" in time_obj:
            row["start_time"] = time_obj["start_time"]
        if "end_time" in time_obj:
            row["end_time"] = time_obj["end_time"]
        if "target" in time_obj:
            row["target"] = time_obj["target"]
        if "repeat_strategy" in time_obj:
            row["repeat_strategy"] = time_obj["repeat_strategy"]
        if "timezone" in time_obj:
            row["timezone"] = time_obj["timezone"]
        timezone = pytz.timezone(row["timezone"])
        row = await conn.fetchrow(
            "UPDATE time_restriction SET start_time = $1, end_time = $2, target = $3, repeat_strategy = $4, timezone = $5 WHERE restriction_id = $6 AND id = $7 RETURNING *;",
            date_to_db(row["start_time"], timezone),
            date_to_db(row["end_time"], timezone),
            row["target"],
            row["repeat_strategy"],
            row["timezone"],
            row["restriction_id"],
            row["id"],
        )
        return TimeRestriction.load_from_db(row)
