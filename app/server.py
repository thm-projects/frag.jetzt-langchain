from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langserve import add_routes
from fastapi.middleware.cors import CORSMiddleware
import os
from app.security.oauth2 import DEPENDENCIES, per_req_config_modifier
from app.routes.keywords import chain as keyword_chain

app = FastAPI()

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

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
