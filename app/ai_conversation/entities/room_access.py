from datetime import datetime
from typing import Optional
from uuid import UUID
from app.ai_conversation.db_decorator import entity
from dataclasses import dataclass


@entity
@dataclass
class RoomAccess:
    id: Optional[UUID]
    room_id: UUID
    account_id: UUID
    role: str
    updated_at: datetime
    last_visit: datetime = datetime.now()
    created_at: datetime = datetime.now()
