from app.ai_conversation.ai_conversation import get_connection_pool
from app.ai_conversation.db import load_file
from enum import StrEnum, auto


class AdminRole(StrEnum):
    ADMIN_DASHBORAD = "admin-dashboard"
    ADMIN_ALL_ROOMS_OWNER = "admin-all-rooms-owner"
    UNKNOWN = auto()

    @classmethod
    def _missing_(cls, _):
        return AdminRole.UNKNOWN


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
    async with get_connection_pool().acquire() as conn:
        v = await conn.fetchval(role_statement, account_id, room_id)
        return Role(v)


async def get_admin_roles(account_id: str) -> list[AdminRole]:
    async with get_connection_pool().acquire() as conn:
        v = await conn.fetch(
            "SELECT role FROM account_keycloak_role WHERE account_id = $1 AND role IN ('admin-dashboard', 'admin-all-rooms-owner');",
            account_id,
        )
        v = v or []
        return [AdminRole(val) for val in v]
