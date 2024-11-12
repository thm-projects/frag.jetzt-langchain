from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.ai_conversation.db_decorator import entity


@entity
@dataclass
class Room:
    id: Optional[UUID]
    owner_id: UUID
    short_id: str
    name: str
    description: Optional[str]
    direct_send: bool
    threshold: int
    tag_cloud_settings: Optional[str]
    moderator_room_reference: Optional[UUID]
    updated_at: Optional[datetime]
    language: Optional[str]
    closed: bool = False
    bonus_archive_active: bool = True
    questions_blocked: bool = False
    blacklist: str = "[]"
    profanity_filter: str = "LANGUAGE_SPECIFIC"
    blacklist_active: bool = True
    created_at: datetime = datetime.now()
    last_visit_creator: datetime = datetime.now()
    conversation_depth: Optional[int] = 3
    quiz_active: Optional[bool] = True
    brainstorming_active: Optional[bool] = True
    livepoll_active: bool = True
    keyword_extraction_active: bool = True
    radar_active: bool = True
    focus_active: bool = True
    chat_gpt_active: bool = True
    mode: str = "ARS"
