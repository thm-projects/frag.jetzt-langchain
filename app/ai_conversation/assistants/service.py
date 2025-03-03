from uuid import UUID
from app.ai_conversation.ai_conversation import get_connection_pool
from app.ai_conversation.assistants.models import (
    AssistantFile,
    AssistantShareType,
    InputAssistant,
    OutputAssistant,
    UploadedFile,
    WrappedAssistant,
)
from app.ai_conversation.services.role_checker import AdminRole, Role


async def get_generic_assistant(config: dict, assistant_id: UUID) -> WrappedAssistant:
    room_id = config["configurable"]["room"]["id"]
    account_id = config["configurable"]["user_info"]["id"]
    roles = config["configurable"]["user_info"]["admin_roles"]
    is_admin = AdminRole.ADMIN_DASHBORAD in roles
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetchrow(
            "SELECT * FROM assistant WHERE id = $1;", assistant_id
        )
        if not data:
            return None
        assistant: OutputAssistant = OutputAssistant.load_from_db(data)
        # Ensure assistant can be used
        if assistant.account_id is not None:
            if (
                account_id != assistant.account_id
                and assistant.share_type == AssistantShareType.MINIMAL
            ):
                return None
        elif assistant.room_id is not None:
            if room_id != assistant.room_id:
                return None
        else:
            if not is_admin and assistant.share_type == AssistantShareType.MINIMAL:
                return None

        return (await load_transient_fields(conn, [assistant]))[0]


async def load_transient_fields(
    conn, assistants: list[OutputAssistant]
) -> list[WrappedAssistant]:
    data = await conn.fetch(
        "SELECT * FROM assistant_file WHERE assistant_id IN (SELECT unnest($1::uuid[]));",
        [a.id for a in assistants],
    )
    files: list[AssistantFile] = [AssistantFile.load_from_db(row) for row in data]
    data = await conn.fetch(
        "SELECT * FROM uploaded_file WHERE id IN (SELECT unnest($1::uuid[]));",
        [f.uploaded_file_id for f in files],
    )
    file_refs = [UploadedFile.load_from_db(row) for row in data]
    file_refs = {x.id: x for x in file_refs}
    return [
        WrappedAssistant(
            a,
            [
                (f, file_refs[f.uploaded_file_id])
                for f in files
                if f.assistant_id == a.id
            ],
        )
        for a in assistants
    ]


async def create_user_assistant(
    config: dict, assistant: InputAssistant
) -> OutputAssistant:
    account_id = config["configurable"]["user_info"]["id"]
    if not account_id:
        raise ValueError("Invalid account id")
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetchrow(
            "INSERT INTO assistant(account_id, name, description, instruction, override_json_settings, model_name, provider_list, share_type) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *;",
            account_id,
            assistant.name,
            assistant.description,
            assistant.instruction,
            assistant.override_json_settings,
            assistant.model_name,
            assistant.provider_list,
            assistant.share_type,
        )
        return OutputAssistant.load_from_db(data)


async def list_user_assistants(config: dict) -> list[OutputAssistant]:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetch(
            "SELECT * FROM assistant WHERE account_id = $1;", account_id
        )
        assistants: list[OutputAssistant] = [
            OutputAssistant.load_from_db(row) for row in data
        ]
        return await load_transient_fields(conn, assistants)


async def delete_user_assistant(config: dict, assistant_id: UUID) -> None:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = await conn.execute(
            "DELETE FROM assistant WHERE account_id = $1 AND id = $2;",
            account_id,
            assistant_id,
        )
        if not data:
            raise ValueError("Assistant not found")


def patch_assistant(assistant: dict, row: dict) -> dict:
    if "name" in assistant:
        row["name"] = assistant["name"]
    if "description" in assistant:
        row["description"] = assistant["description"]
    if "instruction" in assistant:
        row["instruction"] = assistant["instruction"]
    if "override_json_settings" in assistant:
        row["override_json_settings"] = assistant["override_json_settings"]
    if "model_name" in assistant:
        row["model_name"] = assistant["model_name"]
    if "provider_list" in assistant:
        row["provider_list"] = assistant["provider_list"]
    if "share_type" in assistant:
        row["share_type"] = assistant["share_type"]
    return row


async def patch_user_assistant(
    config: dict, assistant_id: UUID, assistant: dict
) -> OutputAssistant:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetchrow(
            "SELECT * FROM assistant WHERE account_id = $1 AND id = $2;",
            account_id,
            assistant_id,
        )
        if not data:
            raise ValueError("Assistant not found")
        assistant = patch_assistant(assistant, dict(data))
        data = await conn.fetchrow(
            "UPDATE assistant SET name = $1, description = $2, instruction = $3, override_json_settings = $4, model_name = $5, provider_list = $6, share_type = $7 WHERE account_id = $8 AND id = $9 RETURNING *;",
            assistant["name"],
            assistant["description"],
            assistant["instruction"],
            assistant["override_json_settings"],
            assistant["model_name"],
            assistant["provider_list"],
            assistant["share_type"],
            account_id,
            assistant_id,
        )
        if not data:
            raise ValueError("Assistant not found")
        return OutputAssistant.load_from_db(data)


async def add_user_assistant_files(config: dict, assistant_id: UUID, files: list[UUID]):
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetchrow(
            "SELECT * FROM assistant WHERE account_id = $1 AND id = $2;",
            account_id,
            assistant_id,
        )
        if not data:
            raise ValueError("Assistant not found")
        file_list = await conn.fetch(
            "SELECT id FROM uploaded_file WHERE id IN (SELECT unnest($1::uuid[])) AND account_id = $2;",
            files,
            account_id,
        )
        if len(file_list) != len(files):
            raise ValueError("Not all files were found")
        await conn.executemany(
            "INSERT INTO assistant_file(assistant_id, uploaded_file_id) VALUES ($1, $2);",
            [(assistant_id, v["id"]) for v in file_list],
        )
        return True


async def get_user_assistant_files(
    config: dict, assistant_id: UUID
) -> list[AssistantFile]:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetchrow(
            "SELECT * FROM assistant WHERE account_id = $1 AND id = $2;",
            account_id,
            assistant_id,
        )
        if not data:
            raise ValueError("Assistant not found")
        data = await conn.fetch(
            "SELECT * FROM assistant_file WHERE assistant_id = $1;", assistant_id
        )
        return [AssistantFile.load_from_db(row) for row in data]


async def delete_user_assistant_file(
    config: dict, assistant_id: UUID, file_ids: list[UUID]
):
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetchrow(
            "SELECT * FROM assistant WHERE account_id = $1 AND id = $2;",
            account_id,
            assistant_id,
        )
        if not data:
            raise ValueError("Assistant not found")
        data = await conn.execute(
            "DELETE FROM assistant_file WHERE assistant_id = $1 AND uploaded_file_id IN (SELECT unnest($2::uuid[]));",
            assistant_id,
            file_ids,
        )
        if not data:
            raise ValueError("File not present")


async def create_room_assistant(
    config: dict, assistant: InputAssistant
) -> OutputAssistant:
    room_id = config["configurable"]["room"]["id"]
    role = config["configurable"]["role"]
    if role not in [Role.CREATOR, Role.MODERATOR]:
        raise ValueError("You must be at least Moderator!")
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetchrow(
            "INSERT INTO assistant(room_id, name, description, instruction, override_json_settings, model_name, provider_list, share_type) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *;",
            room_id,
            assistant.name,
            assistant.description,
            assistant.instruction,
            assistant.override_json_settings,
            assistant.model_name,
            assistant.provider_list,
            assistant.share_type,
        )
        return OutputAssistant.load_from_db(data)


async def list_room_assistants(config: dict) -> list[OutputAssistant]:
    room_id = config["configurable"]["room"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetch("SELECT * FROM assistant WHERE room_id = $1;", room_id)
        assistants: list[OutputAssistant] = [
            OutputAssistant.load_from_db(row) for row in data
        ]
        return await load_transient_fields(conn, assistants)


async def delete_room_assistant(config: dict, assistant_id: UUID) -> None:
    room_id = config["configurable"]["room"]["id"]
    role = config["configurable"]["role"]
    if role not in [Role.CREATOR, Role.MODERATOR]:
        raise ValueError("You must be at least Moderator!")
    async with get_connection_pool().acquire() as conn:
        data = await conn.execute(
            "DELETE FROM assistant WHERE room_id = $1 AND id = $2;",
            room_id,
            assistant_id,
        )
        if not data:
            raise ValueError("Assistant not found")


async def patch_room_assistant(
    config: dict, assistant_id: UUID, assistant: dict
) -> OutputAssistant:
    room_id = config["configurable"]["room"]["id"]
    role = config["configurable"]["role"]
    if role not in [Role.CREATOR, Role.MODERATOR]:
        raise ValueError("You must be at least Moderator!")
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetchrow(
            "SELECT * FROM assistant WHERE room_id = $1 and id = $2;",
            room_id,
            assistant_id,
        )
        if not data:
            raise ValueError("No assistant found")
        assistant = patch_assistant(assistant, dict(data))
        data = await conn.fetchrow(
            "UPDATE assistant SET name = $1, description = $2, instruction = $3, override_json_settings = $4, model_name = $5, provider_list = $6, share_type = $7 WHERE room_id = $8 AND id = $9 RETURNING *;",
            assistant["name"],
            assistant["description"],
            assistant["instruction"],
            assistant["override_json_settings"],
            assistant["model_name"],
            assistant["provider_list"],
            assistant["share_type"],
            room_id,
            assistant_id,
        )
        if not data:
            raise ValueError("Assistant not found")
        return OutputAssistant.load_from_db(data)


async def add_room_assistant_files(config: dict, assistant_id: UUID, files: list[UUID]):
    account_id = config["configurable"]["user_info"]["id"]
    room_id = config["configurable"]["room"]["id"]
    role = config["configurable"]["role"]
    if role not in [Role.CREATOR, Role.MODERATOR]:
        raise ValueError("You must be at least Moderator!")
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetchrow(
            "SELECT * FROM assistant WHERE room_id = $1 and id = $2;",
            room_id,
            assistant_id,
        )
        if not data:
            raise ValueError("No assistant found")
        file_list = await conn.fetch(
            "SELECT id FROM uploaded_file WHERE id IN (SELECT unnest($1::uuid[])) AND account_id = $2;",
            files,
            account_id,
        )
        if len(file_list) != len(files):
            raise ValueError("Not all files were found")
        await conn.executemany(
            "INSERT INTO assistant_file(assistant_id, uploaded_file_id) VALUES ($1, $2);",
            [(assistant_id, v["id"]) for v in file_list],
        )
        return True


async def get_room_assistant_files(
    config: dict, assistant_id: UUID
) -> list[AssistantFile]:
    role = config["configurable"]["role"]
    # Everyone inside the room can access the files
    if role not in [Role.PARTICIPANT, Role.MODERATOR, Role.CREATOR]:
        raise ValueError("You are not part of the room")
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetch(
            "SELECT * FROM assistant_file WHERE assistant_id = $1;", assistant_id
        )
        return [AssistantFile.load_from_db(row) for row in data]


async def delete_room_assistant_file(
    config: dict, assistant_id: UUID, file_ids: list[UUID]
):
    room_id = config["configurable"]["room"]["id"]
    role = config["configurable"]["role"]
    if role not in [Role.CREATOR, Role.MODERATOR]:
        raise ValueError("You must be at least Moderator!")
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetchrow(
            "SELECT * FROM assistant WHERE room_id = $1 and id = $2;",
            room_id,
            assistant_id,
        )
        if not data:
            raise ValueError("No assistant found")
        data = await conn.execute(
            "DELETE FROM assistant_file WHERE assistant_id = $1 AND uploaded_file_id IN (SELECT unnest($2::uuid[]))",
            assistant_id,
            file_ids,
        )
        if not data:
            raise ValueError("File not present")


async def create_platform_assistant(
    config: dict, assistant: InputAssistant
) -> OutputAssistant:
    roles = config["configurable"]["user_info"]["admin_roles"]
    can_create = AdminRole.ADMIN_DASHBORAD in roles
    if not can_create:
        raise ValueError("You must be at least Admin!")
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetchrow(
            "INSERT INTO assistant(name, description, instruction, override_json_settings, model_name, provider_list, share_type) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *;",
            assistant.name,
            assistant.description,
            assistant.instruction,
            assistant.override_json_settings,
            assistant.model_name,
            assistant.provider_list,
            assistant.share_type,
        )
        return OutputAssistant.load_from_db(data)


async def list_platform_assistant() -> list[OutputAssistant]:
    # Everyone can see platform assistants
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetch(
            "SELECT * FROM assistant WHERE room_restriction_id IS NULL AND account_id IS NULL;"
        )
        assistants: list[OutputAssistant] = [
            OutputAssistant.load_from_db(row) for row in data
        ]
        return await load_transient_fields(conn, assistants)


async def delete_platform_assistant(config: dict, assistant_id: UUID) -> None:
    roles = config["configurable"]["user_info"]["admin_roles"]
    can_delete = AdminRole.ADMIN_DASHBORAD in roles
    if not can_delete:
        raise ValueError("You must be at least Admin!")
    async with get_connection_pool().acquire() as conn:
        data = await conn.execute(
            "DELETE FROM assistant WHERE id = $1 AND room_restriction_id IS NULL AND account_id IS NULL;",
            assistant_id,
        )
        if not data:
            raise ValueError("Assistant not found")


async def patch_platform_assistant(
    config: dict, assistant_id: UUID, assistant: dict
) -> None:
    roles = config["configurable"]["user_info"]["admin_roles"]
    can_delete = AdminRole.ADMIN_DASHBORAD in roles
    if not can_delete:
        raise ValueError("You must be at least Admin!")
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetchrow(
            "SELECT * FROM assistant WHERE id = $1 AND room_restriction_id IS NULL AND account_id IS NULL;",
            assistant_id,
        )
        if not data:
            raise ValueError("No assistant found")
        assistant = patch_assistant(assistant, dict(data))
        data = await conn.fetchrow(
            "UPDATE assistant SET name = $1, description = $2, instruction = $3, override_json_settings = $4, model_name = $5, provider_list = $6, share_type = $7 WHERE id = $8 RETURNING *;",
            assistant["name"],
            assistant["description"],
            assistant["instruction"],
            assistant["override_json_settings"],
            assistant["model_name"],
            assistant["provider_list"],
            assistant["share_type"],
            assistant_id,
        )
        if not data:
            raise ValueError("Assistant not found")
        return OutputAssistant.load_from_db(data)


async def add_platform_assistant_files(
    config: dict, assistant_id: UUID, files: list[UUID]
):
    account_id = config["configurable"]["user_info"]["id"]
    roles = config["configurable"]["user_info"]["admin_roles"]
    can_use = AdminRole.ADMIN_DASHBORAD in roles
    if not can_use:
        raise ValueError("You must be at least Admin!")
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetchrow(
            "SELECT * FROM assistant WHERE id = $1 AND room_restriction_id IS NULL AND account_id IS NULL;",
            assistant_id,
        )
        if not data:
            raise ValueError("No assistant found")
        file_list = await conn.fetch(
            "SELECT id FROM uploaded_file WHERE id IN (SELECT unnest($1::uuid[])) AND account_id = $2;",
            files,
            account_id,
        )
        if len(file_list) != len(files):
            raise ValueError("Not all files were found")
        await conn.executemany(
            "INSERT INTO assistant_file(assistant_id, uploaded_file_id) VALUES ($1, $2);",
            [(assistant_id, v["id"]) for v in file_list],
        )
        return True


async def get_platform_assistant_files(
    _: dict, assistant_id: UUID
) -> list[AssistantFile]:
    # Everyone inside the platform can access the files
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetch(
            "SELECT * FROM assistant_file WHERE assistant_id = $1;", assistant_id
        )
        return [AssistantFile.load_from_db(row) for row in data]


async def delete_platform_assistant_file(
    config: dict, assistant_id: UUID, file_ids: list[UUID]
):
    roles = config["configurable"]["user_info"]["admin_roles"]
    can_use = AdminRole.ADMIN_DASHBORAD in roles
    if not can_use:
        raise ValueError("You must be at least Admin!")
    async with get_connection_pool().acquire() as conn:
        data = await conn.fetchrow(
            "SELECT * FROM assistant WHERE id = $1 AND room_restriction_id IS NULL AND account_id IS NULL;",
            assistant_id,
        )
        if not data:
            raise ValueError("No assistant found")
        data = await conn.execute(
            "DELETE FROM assistant_file WHERE assistant_id = $1 AND uploaded_file_id IN (SELECT unnest($2::uuid[]));",
            assistant_id,
            file_ids,
        )
        if not data:
            raise ValueError("File not present")
