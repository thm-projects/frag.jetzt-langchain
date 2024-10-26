from fastapi import FastAPI, status, HTTPException
from fastapi.responses import RedirectResponse
from langserve import add_routes
from langchain_openai import ChatOpenAI
from langchain_core.runnables import ConfigurableField
from fastapi.middleware.cors import CORSMiddleware
import os
from app.security.oauth2 import DEPENDENCIES, per_req_config_modifier
from app.routes.utils import select_model

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


def test(input, config):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="You can not do this"
    )


# Edit this to add the chain you want to add
add_routes(
    app,
    ChatOpenAI(
        api_key="sk-proj-92ZvpKzkPqIWGCESK2mdT3BlbkFJN5yuKcxxZaYaklYFAfwJ",
        model="gpt-4",
    ).configurable_fields(
        temperature=ConfigurableField(
            id="api_key",
            name="api_key",
            description="API Key for OpenAI",
        ),
    ),
    path="/chat",
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
