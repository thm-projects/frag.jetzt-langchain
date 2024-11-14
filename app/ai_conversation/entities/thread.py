from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.ai_conversation.db_decorator import entity


class ThreadShareType(StrEnum):
    NONE = "NONE"
    CHAT_VIEW = "CHAT_VIEW"
    CHAT_COPY = "CHAT_COPY"
    THREAD_VIEW = "THREAD_VIEW"
    THREAD_COPY = "THREAD_COPY"
    SYNC_VIEW = "SYNC_VIEW"
    SYNC_COPY = "SYNC_COPY"


@entity
@dataclass
class Thread:
    id: UUID
    room_id: UUID
    account_id: UUID
    name: str
    share_type: ThreadShareType = ThreadShareType.NONE
    created_at: datetime = datetime.now()
    updated_at: datetime = None
