

from app.ai_conversation.ai_conversation import get_connection_pool
from app.ai_conversation.restrictions.models import Restrictions


async def create_restrictions() -> Restrictions:
    async with get_connection_pool().acquire() as conn:
        data = conn.fetchrow("INSERT INTO restrictions(created_at) VALUES (NOW()) RETURNING *;")
        if not data:
            raise ValueError("Creation failed")
        return Restrictions.load_from_db(data)


