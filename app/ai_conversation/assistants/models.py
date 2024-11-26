from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.ai_conversation.db_decorator import entity


class AssistantShareType(StrEnum):
    MINIMAL = "MINIMAL"
    VIEWABLE = "VIEWABLE"
    COPYABLE = "COPYABLE"


@dataclass
class InputAssistant:
    name: str
    description: str
    instruction: str
    override_json_settings: str
    model_name: str
    provider_list: str
    share_type: AssistantShareType


@entity
@dataclass
class OutputAssistant:
    id: UUID
    room_id: UUID
    account_id: UUID
    name: str
    description: str
    instruction: str
    override_json_settings: str
    model_name: str
    provider_list: str
    share_type: AssistantShareType
    created_at: datetime
    updated_at: datetime


@entity
@dataclass
class AssistantFile:
    assistant_id: UUID
    uploaded_file_id: UUID
    created_at: datetime


@entity
@dataclass
class UploadedFile:
    id: UUID
    content_id: UUID
    account_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


@dataclass
class WrappedAssistant:
    assistant: OutputAssistant
    files: list[tuple[AssistantFile, UploadedFile]]
