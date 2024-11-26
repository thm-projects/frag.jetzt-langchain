from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.ai_conversation.db_decorator import entity


@dataclass
class InputRoomAISetting:
    room_id: UUID
    restriction_id: Optional[UUID]
    api_setup_id: Optional[UUID]
    allow_global_assistants: bool
    allow_user_assistants: bool


@entity
@dataclass
class RoomAISetting:
    id: UUID
    room_id: UUID
    restriction_id: Optional[UUID]
    api_setup_id: Optional[UUID]
    api_voucher_id: Optional[UUID]
    allow_global_assistants: bool
    allow_user_assistants: bool
    created_at: datetime
    updated_at: datetime

@dataclass
class InputAPIVoucher:
    voucher: str
    restriction_id: UUID


@entity
@dataclass
class APIVoucher:
    id: UUID
    room_id: Optional[UUID]
    voucher: str
    restriction_id: UUID
    created_at: datetime
    updated_at: datetime