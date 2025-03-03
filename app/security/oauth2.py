from typing import Annotated, Dict
from uuid import UUID
from fastapi import Depends, status, Header, HTTPException, Request
import jwt
from jwt.exceptions import InvalidTokenError
import os
import base64

from app.ai_conversation.ai_conversation import get_connection_pool
from app.ai_conversation.services.role_checker import get_admin_roles, get_role

SECRET_KEY = os.getenv("SECRET_KEY", "")
SECRET_ALGORITHM = os.getenv("SECRET_ALGORITHM", "HS256")
if not SECRET_KEY or not SECRET_ALGORITHM:
    exit("SECRET_KEY and SECRET_ALGORITHM is required")
SECRET_KEY = base64.b64decode(SECRET_KEY)

# temporary
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    exit("OPENAI_API_KEY is currently required")


async def verify_room_id(
    request: Request,
    room_id: Annotated[
        UUID, Header(alias="Room-Id", description="Id of the Room")
    ] = "",
):
    async with get_connection_pool().acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM room WHERE id = $1;", room_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid room id",
            )
        request.state.room = row
        request.state.role = await get_role(request.state.user_id, row["id"])


async def verify_token(
    request: Request,
    token: Annotated[
        str,
        Header(
            alias="Authorization",
            description="Token from frag.jetzt Backend",
            example="Bearer eyJhbGciOiJIUzI1NiJ9.eyJoIjoxfQ.0KodOLycKkTh-Zq0hNu2QdzKxkQJCkx1FgSOleBQchI",
        ),
    ] = "",
):
    path = request.url.path
    if (
        path.endswith("/config_schema")
        or path.endswith("/input_schema")
        or path.endswith("/output_schema")
    ):
        request.state.user_id = None
        request.state.user_type = None
        return
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token or not token.startswith("Bearer "):
        raise exception
    try:
        token = token[7:]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[SECRET_ALGORITHM])
        request.state.user_id = payload["sub"]
        request.state.user_type = payload["type"]
    except InvalidTokenError:
        raise exception
    request.state.user_admin_roles = await get_admin_roles(payload["sub"])


async def per_req_config_modifier(config: Dict, request: Request) -> Dict:
    """Modify the config for each request."""
    config["configurable"]["user_info"] = {
        "id": request.state.user_id,
        "type": request.state.user_type,
        "admin_roles": request.state.user_admin_roles,
    }
    config["configurable"]["room"] = (
        request.state.room if "room" in request.state._state else None
    )
    config["configurable"]["role"] = (
        request.state.role if "role" in request.state._state else None
    )
    config["configurable"]["provider"] = "openai"
    config["configurable"]["api_obj"] = {
        "api_key": API_KEY,
        "model": "gpt-4o-mini",
    }
    return config


DEPENDENCIES = [Depends(verify_token)]

ROOM_DEPENDENCIES = [Depends(verify_token), Depends(verify_room_id)]
