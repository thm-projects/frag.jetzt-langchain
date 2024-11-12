from ai_conversation import async_connection_pool
from db import load_file
from enum import StrEnum, auto


class Role(StrEnum):
    CREATOR = "CREATOR"
    MODERATOR = "MODERATOR"
    PARTICIPANT = "PARTICIPANT"
    NOT_VISITED = "NULL"
    NO_VALID_ROOM = auto()
    UNKNOWN = auto()

    @classmethod
    def _missing_(cls, value):
        if value is None:
            return Role.NO_VALID_ROOM
        elif value == "EXECUTIVE_MODERATOR":
            return Role.MODERATOR
        elif value == "EDITING_MODERATOR":
            return Role.MODERATOR
        return Role.UNKNOWN


role_statement = load_file("find_role")


async def get_role(account_id: str, room_id: str):
    with await async_connection_pool.acquire() as conn:
        v = await conn.fetchval(role_statement, account_id, room_id)
        return Role(v)
