from datetime import datetime
from typing import Optional
from uuid import UUID
from app.ai_conversation.db_decorator import entity
from dataclasses import dataclass


@entity
@dataclass
class Account:
    id: Optional[UUID]
    email: Optional[str]
    last_login: Optional[datetime]
    last_active: Optional[datetime]
    updated_at: Optional[datetime]
    keycloak_id: Optional[UUID]
    keycloak_user_id: Optional[UUID]
    created_at: datetime = datetime.now()
