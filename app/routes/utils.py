from fastapi import HTTPException, status
from langchain_ai21 import ChatAI21
from langchain_anthropic import ChatAnthropic
from langchain_cohere import ChatCohere
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_mistralai import ChatMistralAI
from langchain_fireworks import ChatFireworks
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_together import ChatTogether
from langchain_groq import ChatGroq
from langchain_aws import ChatBedrock, ChatBedrockConverse
from langchain_upstage import ChatUpstage

DEFAULT_VALUES = {}
MANDATORY_FIELDS = {}

# TODO: Aleph alpha
# could be added: Databricks, VertexAI,
# StabilityAI? : Replicate
# Snowflake? : https://python.langchain.com/docs/integrations/chat/snowflake/
# IBM WatsonX? : https://python.langchain.com/docs/integrations/chat/ibm_watsonx/

def _build_defaults():
    # anthropic
    m = ChatAnthropic(api_key="a", model="claude-3-5-sonnet-20240620")
    MANDATORY_FIELDS["anthropic"] = [
        {"name": "api_key", "type": "str"},
        {"name": "model", "type": "str"},
    ]
    DEFAULT_VALUES["anthropic"] = {
        "temperature": {"type": "float|null", "default": m.temperature},
        "top_k": {"type": "int|null", "default": m.top_k},
        "top_p": {"type": "float|null", "default": m.top_p},
        "max_tokens": {"type": "int", "default": m.max_tokens},
    }
    # mistral
    m = ChatMistralAI(api_key="a")
    MANDATORY_FIELDS["mistral"] = [
        {"name": "api_key", "type": "str"},
    ]
    DEFAULT_VALUES["mistral"] = {
        "model": {"type": "str", "default": m.model},
        "temperature": {"type": "float", "default": m.temperature},
        "top_p": {"type": "float", "default": m.top_p},
        "max_tokens": {"type": "int|null", "default": m.max_tokens},
    }
    # fireworks
    m = ChatFireworks(
        api_key="a", model="accounts/fireworks/models/llama-v3-70b-instruct"
    )
    MANDATORY_FIELDS["fireworks"] = [
        {"name": "api_key", "type": "str"},
        {"name": "model", "type": "str"},
    ]
    DEFAULT_VALUES["fireworks"] = {
        "temperature": {"type": "float", "default": m.temperature},
        "max_tokens": {"type": "int|null", "default": m.max_tokens},
    }
    # azure
    # Either API Key or AD Token or AD Token Provider (a bit more to do, if needed)
    m = AzureChatOpenAI(api_version="2020-09-03", api_key="a", azure_endpoint="a")
    MANDATORY_FIELDS["azure"] = [
        {"name": "azure_endpoint", "type": "str"},
        {"name": "api_version", "type": "str"},
        [{"name": "api_key", "type": "str"}, {"name": "azure_ad_token", "type": "str"}],
    ]
    DEFAULT_VALUES["azure"] = {
        "deployment_name": {"type": "str|null", "default": m.deployment_name},
        "model_version": {"type": "str", "default": m.model_version},
        "model_name": {"type": "str|null", "default": m.model_name},
        "temperature": {"type": "float", "default": m.temperature},
        "openai_organization": {"type": "str|null", "default": m.openai_organization},
        "max_tokens": {"type": "int|null", "default": m.max_tokens},
    }
    # openai
    m = ChatOpenAI(api_key="a")
    MANDATORY_FIELDS["openai"] = [
        {"name": "api_key", "type": "str"},
    ]
    DEFAULT_VALUES["openai"] = {
        "model": {"type": "str", "default": m.model_name},
        "openai_organization": {"type": "str|null", "default": m.openai_organization},
        "temperature": {"type": "float", "default": m.temperature},
        "frequency_penalty": {"type": "float|null", "default": m.frequency_penalty},
        "presence_penalty": {"type": "float|null", "default": m.presence_penalty},
        "top_p": {"type": "float|null", "default": m.top_p},
        "max_tokens": {"type": "int|null", "default": m.max_tokens},
    }
    # together
    m = ChatTogether(api_key="a")
    MANDATORY_FIELDS["together"] = [
        {"name": "api_key", "type": "str"},
    ]
    DEFAULT_VALUES["together"] = {
        "model": {"type": "str", "default": m.model_name},
        "temperature": {"type": "float", "default": m.temperature},
        "frequency_penalty": {
            "type": "float|null",
            "default": m.frequency_penalty,
        },  # valid?
        "presence_penalty": {
            "type": "float|null",
            "default": m.presence_penalty,
        },  # valid?
        "top_p": {"type": "float|null", "default": m.top_p},  # valid?
        "max_tokens": {"type": "int|null", "default": m.max_tokens},
    }
    # vertex # NOT ALLOWED
    # TODO: Is it possible to run multiple instances?
    # See google-genai Credentials
    # google-genai
    # credentials (TODO: https://cloud.google.com/docs/authentication/provide-credentials-adc?hl=de#how-to) or api_key
    m = ChatGoogleGenerativeAI(api_key="a", model="gemini-1.5-pro")
    MANDATORY_FIELDS["google-genai"] = [
        {"name": "api_key", "type": "str"},
        {"name": "model", "type": "str"},
    ]
    DEFAULT_VALUES["google-genai"] = {
        "temperature": {"type": "float", "default": m.temperature},
        "top_p": {"type": "float|null", "default": m.top_p},
        "top_k": {"type": "int|null", "default": m.top_k},
        "max_tokens": {"type": "int|null", "default": m.max_output_tokens},
    }
    # groq
    m = ChatGroq(api_key="a")
    MANDATORY_FIELDS["groq"] = [
        {"name": "api_key", "type": "str"},
    ]
    DEFAULT_VALUES["groq"] = {
        "model": {"type": "str", "default": m.model_name},
        "temperature": {"type": "float", "default": m.temperature},
        "max_tokens": {"type": "int|null", "default": m.max_tokens},
    }
    # cohere
    m = ChatCohere(cohere_api_key="a")
    MANDATORY_FIELDS["cohere"] = [
        {"name": "cohere_api_key", "type": "str"},
    ]
    # docs say also: frequency_penalty, presence_penalty, k, p, max_tokens
    DEFAULT_VALUES["cohere"] = {
        "model": {"type": "str|null", "default": m.model},
        "temperature": {"type": "float|null", "default": m.temperature},
    }
    # bedrock
    # Either use (aws_access_key_id, aws_secret_access_key) or
    # credentials_profile_name (not allowed, https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html) or
    # (aws_session_token, aws_access_key_id, aws_secret_access_key)
    m = ChatBedrock(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0", region_name="eu-west"
    )
    MANDATORY_FIELDS["bedrock"] = [
        {"name": "model_id", "type": "str"},
        {"name": "region_name", "type": "str"},
        [
            [
                {"name": "aws_access_key_id", "type": "str"},
                {"name": "aws_secret_access_key", "type": "str"},
            ],
            [
                {"name": "aws_access_key_id", "type": "str"},
                {"name": "aws_secret_access_key", "type": "str"},
                {"name": "aws_session_token", "type": "str"},
            ],
        ],
    ]
    DEFAULT_VALUES["bedrock"] = {
        "model_kwargs": {"type": "dict|null", "default": m.model_kwargs},
        "endpoint_url": {"type": "str|null", "default": m.endpoint_url},
        "provider": {"type": "str|null", "default": m.provider},
    }
    # bedrock-converse
    # Either use (aws_access_key_id, aws_secret_access_key) or
    # credentials_profile_name (https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html) or
    # (aws_session_token, aws_access_key_id, aws_secret_access_key)
    m = ChatBedrockConverse(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0", region_name="eu-west"
    )
    MANDATORY_FIELDS["bedrock-converse"] = [
        {"name": "model_id", "type": "str"},
        {"name": "region_name", "type": "str"},
        [
            [
                {"name": "aws_access_key_id", "type": "str"},
                {"name": "aws_secret_access_key", "type": "str"},
            ],
            [
                {"name": "aws_access_key_id", "type": "str"},
                {"name": "aws_secret_access_key", "type": "str"},
                {"name": "aws_session_token", "type": "str"},
            ],
        ],
    ]
    DEFAULT_VALUES["bedrock-converse"] = {
        "temperature": {"type": "float|null", "default": m.temperature},
        "top_p": {"type": "float|null", "default": m.top_p},
        "endpoint_url": {"type": "str|null", "default": m.endpoint_url},
        "provider": {"type": "str|null", "default": m.provider},
        "max_tokens": {"type": "int|null", "default": m.max_tokens},
    }
    # huggingface, remotely (HuggingFaceEndpoint)
    m = HuggingFaceEndpoint(
        endpoint_url="http://localhost:8000",
    )
    MANDATORY_FIELDS["huggingface"] = [
        [
            {"name": "endpoint_url", "type": "str"},
            [
                {"name": "endpoint_url", "type": "str"},
                {"name": "huggingfacehub_api_token", "type": "str"},
            ],
            [
                {"name": "repo_id", "type": "str"},
                {"name": "huggingfacehub_api_token", "type": "str"},
            ],
            [
                {"name": "model", "type": "str"},
                {"name": "huggingfacehub_api_token", "type": "str"},
            ],
        ]
    ]
    DEFAULT_VALUES["huggingface"] = {
        "temperature": {"type": "float|null", "default": m.temperature},
        "top_k": {"type": "int|null", "default": m.top_k},
        "top_p": {"type": "float|null", "default": m.top_p},
        "typical_p": {"type": "float|null", "default": m.typical_p},
        "repetition_penalty": {"type": "float|null", "default": m.repetition_penalty},
        "model_kwargs": {"type": "dict|null", "default": m.model_kwargs},
        "max_tokens": {"type": "int", "default": m.max_new_tokens},
    }
    # huggingface-local, locally (HuggingFacePipeline)
    # nvidia, remotly or self-hosted via nim
    m = ChatNVIDIA(nvidia_api_key="a")
    MANDATORY_FIELDS["nvidia"] = [
        [
            {"name": "base_url", "type": "str"},
            [
                {"name": "base_url", "type": "str"},
                {"name": "nvidia_api_key", "type": "str"},
            ],
            {"name": "nvidia_api_key", "type": "str"},
        ]
    ]
    DEFAULT_VALUES["nvidia"] = {
        "model": {"type": "str|null", "default": m.model},
        "temperature": {"type": "float|null", "default": m.temperature},
        "top_p": {"type": "float|null", "default": m.top_p},
        "max_tokens": {"type": "int|null", "default": m.max_tokens},
    }
    # ollama, locally
    # llama-cpp, locally
    # ai21
    m = ChatAI21(api_key="a", model="jamba-1.5-mini")
    MANDATORY_FIELDS["ai21"] = [
        {"name": "api_key", "type": "str"},
        {"name": "model", "type": "str"},
    ]
    DEFAULT_VALUES["ai21"] = {
        "temperature": {"type": "float", "default": m.temperature},
        "top_p": {"type": "float", "default": m.top_p},
        "max_tokens": {"type": "int", "default": m.max_tokens},
    }
    # upstage
    m = ChatUpstage(api_key="a")
    MANDATORY_FIELDS["upstage"] = [
        {"name": "api_key", "type": "str"},
    ]
    DEFAULT_VALUES["upstage"] = {
        "model": {"type": "str", "default": m.model_name},
        "temperature": {"type": "float", "default": m.temperature},
        "top_p": {"type": "float", "default": m.top_p},
        "max_tokens": {"type": "int", "default": m.max_tokens},
    }


_build_defaults()

print(DEFAULT_VALUES)


# TODO: Rate limiter & Timeout? / Retry? & Max Tokens?
# https://python.langchain.com/docs/integrations/chat/
def select_model(input, config):
    api_obj = config.get("api_obj") or {}
    api_key = api_obj["api_key"]
    model = api_obj["model"]
    temperature = api_obj.get("temperature")
    top_k = api_obj.get("top_k")
    top_p = api_obj.get("top_p")
    match config["provider"]:
        case "anthropic":
            # https://python.langchain.com/docs/integrations/chat/anthropic/
            return ChatAnthropic(
                api_key=api_key,
                model=model,
                max_retries=0,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
            )
        case "mistral":
            # https://python.langchain.com/docs/integrations/chat/mistralai/
            return ChatMistralAI(
                api_key=api_key,
                model=model,
                max_retries=0,
                temperature=temperature,
                top_p=top_p,
            )
        case "fireworks":
            # https://python.langchain.com/docs/integrations/chat/fireworks/
            return ChatFireworks(
                api_key=api_key,
                model=model,
                max_retries=0,
                temperature=temperature,
            )
        case "azure":
            # https://python.langchain.com/docs/integrations/chat/azure_chat_openai/
            return AzureChatOpenAI(
                azure_endpoint="",
                api_key=api_key,  # or ad_token
                model=model,
                model_version=None,
                max_retries=0,
                temperature=temperature,
            )
        case "openai":
            # https://python.langchain.com/docs/integrations/chat/openai/
            return ChatOpenAI(
                api_key=api_key,
                model=model,
                max_retries=0,
                temperature=temperature,
            )
        case "together":
            # https://python.langchain.com/docs/integrations/chat/together/
            return ChatTogether(
                model="meta-llama/Llama-3-70b-chat-hf",
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                # other params...
            )
        # case "vertex": # NOT ALLOWED
        # https://python.langchain.com/docs/integrations/chat/google_vertex_ai_palm/
        case "google-genai":
            # https://python.langchain.com/docs/integrations/chat/google_generative_ai/
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                # other params...
            )
        case "groq":
            # https://python.langchain.com/docs/integrations/chat/groq/
            return ChatGroq(
                model="mixtral-8x7b-32768",
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                # other params...
            )
        case "cohere":
            return ChatCohere()
        case "bedrock":
            return ChatBedrock(
                model_id="anthropic.claude-3-sonnet-20240229-v1:0",
                model_kwargs=dict(temperature=0),
                # other params...
            )
        case "bedrock-converse":
            return ChatBedrockConverse(
                model="anthropic.claude-3-sonnet-20240229-v1:0",
                temperature=0,
                max_tokens=None,
                # other params...
            )
        case "huggingface":
            llm = HuggingFaceEndpoint(
                repo_id="HuggingFaceH4/zephyr-7b-beta",
                task="text-generation",
                max_new_tokens=512,
                do_sample=False,
                repetition_penalty=1.03,
            )
            return ChatHuggingFace(llm=llm)
        case "nvidia":
            return ChatNVIDIA(
                model="meta/llama3-8b-instruct",
            )
        case "ai21":
            return ChatAI21(
                api_key=api_key,
                model=model,
                temperature=temperature,
                top_p=top_p,
            )
        case "upstage":
            return ChatUpstage(
                api_key=api_key,
                model=model,
                temperature=temperature,
                top_p=top_p,
            )
        case _:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Something went wrong during provider selection",
            )
