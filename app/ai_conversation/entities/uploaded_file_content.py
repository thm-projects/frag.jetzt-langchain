
from app.ai_conversation.db_decorator import entity
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

@entity
@dataclass
class UploadedFileContent:
    id: UUID
    hash: str
    file_ref: UUID
    unprocessed: bool
    created_at: datetime = datetime.now()