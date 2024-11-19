from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langserve import add_routes
from fastapi.middleware.cors import CORSMiddleware
import os
from app.security.oauth2 import DEPENDENCIES, per_req_config_modifier
from app.routes.keywords import chain as keyword_chain
from app.routes.improve import chain as improve_chain
from app.ai_conversation.file_handling.router import router as file_router
from app.ai_conversation.ai_conversation import shutdown, init
from app.ai_conversation.threads.router import router as thread_router
from app.ai_conversation.api.router import router as api_router
from app.ai_conversation.assistants.router import router as assistant_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init()
    yield
    await shutdown()


app = FastAPI(lifespan=lifespan)

ORIGINS = os.getenv("ORIGINS", "").split(",")
ORIGINS.append("localhost")

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

app.include_router(file_router, prefix="/file")
app.include_router(thread_router, prefix="/thread")
app.include_router(api_router, prefix="/api")
app.include_router(assistant_router, prefix="")

# Edit this to add the chain you want to add
add_routes(
    app,
    keyword_chain,
    path="/keyword",
    config_keys=["configurable"],
    enabled_endpoints=[
        "invoke",
        "stream",
        "config_schema",
        "input_schema",
        "output_schema",
    ],
    dependencies=DEPENDENCIES,
    per_req_config_modifier=per_req_config_modifier,
)

add_routes(
    app,
    improve_chain,
    path="/improve",
    config_keys=["configurable"],
    enabled_endpoints=[
        "invoke",
        "stream",
        "config_schema",
        "input_schema",
        "output_schema",
    ],
    dependencies=DEPENDENCIES,
    per_req_config_modifier=per_req_config_modifier,
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
