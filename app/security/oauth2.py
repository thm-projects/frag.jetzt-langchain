from typing import Annotated, Dict
from fastapi import Depends, status, Header, HTTPException, Request
import jwt
from jwt.exceptions import InvalidTokenError
import os
import base64

SECRET_KEY = os.getenv("SECRET_KEY", "")
SECRET_ALGORITHM = os.getenv("SECRET_ALGORITHM", "HS256")
if not SECRET_KEY or not SECRET_ALGORITHM:
    exit("SECRET_KEY and SECRET_ALGORITHM is required")
SECRET_KEY = base64.b64decode(SECRET_KEY)


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
        request.state.payload = None
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


async def per_req_config_modifier(config: Dict, request: Request) -> Dict:
    """Modify the config for each request."""
    config["user_info"] = {}
    config["user_info"]["id"] = request.state.user_id
    config["user_info"]["type"] = request.state.user_type
    return config


DEPENDENCIES = [Depends(verify_token)]
