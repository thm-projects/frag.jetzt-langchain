from fastapi import HTTPException, status
from langchain_ai21 import ChatAI21
from langchain_anthropic import ChatAnthropic
from langchain_cohere import ChatCohere
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_ibm import ChatWatsonx
from ibm_watsonx_ai.foundation_models.schema import TextChatParameters
from langchain_mistralai import ChatMistralAI
from langchain_fireworks import ChatFireworks
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_together import ChatTogether
from langchain_groq import ChatGroq
from langchain_aws import ChatBedrock, ChatBedrockConverse
from langchain_upstage import ChatUpstage
from langchain_community.chat_models import ChatSnowflakeCortex
from langchain_ollama import ChatOllama
import os

DEFAULT_VALUES = {}
MANDATORY_FIELDS = {}
REST_DATA = {}

# could be added: Databricks, VertexAI, Aleph alpha (langchain provides only llms, could use ChatOpenAi with base_url="https://api.aleph-alpha.com/")
# StabilityAI? : Replicate

FRAGJETZT_OLLAMA_ENDPOINT = os.getenv("FRAGJETZT_OLLAMA_ENDPOINT")


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
        "temperature": {"type": "float|null", "default": m.temperature},
        "max_tokens": {"type": "int|null", "default": m.max_tokens},
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
        "task": {"type": "str|null", "default": m.task},
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
    # watsonx
    # m = ChatWatsonx(
    #    url="https://us-south.ml.cloud.ibm.com",
    #    password="a",
    #    username="a",
    #    model_id="a",
    #    instance_id="123",
    # )
    MANDATORY_FIELDS["watsonx"] = [
        {"name": "url", "type": "str"},
        [
            {"name": "apikey", "type": "str"},
            # cloud.ibm.com in url -> only apikey, else others
            [
                {"name": "token", "type": "str"},
                {"name": "instance_id", "type": "str"},
            ],
            [
                {"name": "password", "type": "str"},
                {"name": "username", "type": "str"},
                {"name": "instance_id", "type": "str"},
            ],
            [
                {"name": "apikey", "type": "str"},
                {"name": "username", "type": "str"},
                {"name": "instance_id", "type": "str"},
            ],
        ],
        [
            {"name": "model_id", "type": "str"},
            {"name": "deployment_id", "type": "str"},
        ],
        [
            {"name": "project_id", "type": "str"},
            {"name": "space_id", "type": "str"},
        ],
    ]
    DEFAULT_VALUES["watsonx"] = {
        "version": {"type": "str|null", "default": None},
        "params": {
            "type": [
                {
                    "frequency_penalty": {"type": "float|null", "default": None},
                    "presence_penalty": {"type": "float|null", "default": None},
                    "temperature": {"type": "float|null", "default": None},
                    "top_p": {"type": "float|null", "default": None},
                    "max_tokens": {"type": "int|null", "default": None},
                },
                "null",
            ],
            "default": None,
        },
    }
    # snowflake
    # m = ChatSnowflakeCortex(
    #    snowflake_account="a",
    #    snowflake_username="a",
    #    snowflake_password="a",
    #    snowflake_database="a",
    #    snowflake_schema="a",
    #    snowflake_role="a",
    #    snowflake_warehouse="a",
    # )
    MANDATORY_FIELDS["snowflake"] = [
        {"name": "account", "type": "str"},
        {"name": "username", "type": "str"},
        {"name": "password", "type": "str"},
        {"name": "database", "type": "str"},
        {"name": "schema", "type": "str"},
        {"name": "role", "type": "str"},
        {"name": "warehouse", "type": "str"},
    ]
    DEFAULT_VALUES["snowflake"] = {
        "model": {"type": "str", "default": "snowflake-arctic"},
        "cortex_function": {"type": "str", "default": "complete"},
        "temperature": {"type": "float", "default": 0.7},
        "top_p": {"type": "float|null", "default": None},
        "max_tokens": {"type": "int|null", "default": None},
    }
    # fragjetzt
    if FRAGJETZT_OLLAMA_ENDPOINT:
        MANDATORY_FIELDS["fragjetzt"] = []
        DEFAULT_VALUES["fragjetzt"] = {
            "model": {"type": "str|null", "default": "deepseek-r1:14b"},
            "temperature": {"type": "float|null", "default": None},
            "repeat_penalty": {"type": "float|null", "default": None},
            "seed": {"type": "int|null", "default": None},
            "top_k": {"type": "int|null", "default": None},
            "top_p": {"type": "float|null", "default": None},
            "max_tokens": {"type": "int|null", "default": None},
        }
    # Make rest data
    mandatory_keys = MANDATORY_FIELDS.keys()
    default_values_keys = DEFAULT_VALUES.keys()
    if mandatory_keys != default_values_keys:
        raise ValueError("Keys mismatch")
    for key in mandatory_keys:
        REST_DATA[key] = {
            "mandatory": MANDATORY_FIELDS[key],
            "optional": DEFAULT_VALUES[key],
        }


_build_defaults()


def get_mandatory(provider, key, api_obj):
    if key not in api_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{key} is a mandatory field for {provider}",
        )
    return api_obj[key]


DUMMY = {}


def get_optional(key, api_obj, default_obj, override_value=DUMMY):
    if key in api_obj:
        return api_obj[key]
    if override_value is not DUMMY:
        return override_value
    return default_obj[key]["default"]


# TODO: Rate limiter & Timeout? / Retry? & Max Tokens?
# https://python.langchain.com/docs/integrations/chat/
def select_model(_, config):
    config = config["configurable"]
    # max_tokens = -1 or None for later setting during calculation
    api_obj = config.get("api_obj") or {}
    match config["provider"]:
        case "anthropic":
            # https://python.langchain.com/docs/integrations/chat/anthropic/
            default_obj = DEFAULT_VALUES["anthropic"]
            return ChatAnthropic(
                api_key=get_mandatory("anthropic", "api_key", api_obj),
                model=get_mandatory("anthropic", "model", api_obj),
                temperature=get_optional("temperature", api_obj, default_obj),
                top_k=get_optional("top_k", api_obj, default_obj),
                top_p=get_optional("top_p", api_obj, default_obj),
                max_tokens=get_optional("max_tokens", api_obj, default_obj, -1),
                max_retries=0,
            )
        case "mistral":
            # https://python.langchain.com/docs/integrations/chat/mistralai/
            default_obj = DEFAULT_VALUES["mistral"]
            return ChatMistralAI(
                api_key=get_mandatory("mistral", "api_key", api_obj),
                model=get_optional("model", api_obj, default_obj),
                temperature=get_optional("temperature", api_obj, default_obj),
                top_p=get_optional("top_p", api_obj, default_obj),
                max_tokens=get_optional("max_tokens", api_obj, default_obj, None),
                max_retries=0,
            )
        case "fireworks":
            # https://python.langchain.com/docs/integrations/chat/fireworks/
            default_obj = DEFAULT_VALUES["fireworks"]
            return ChatFireworks(
                api_key=get_mandatory("fireworks", "api_key", api_obj),
                model=get_mandatory("fireworks", "model", api_obj),
                temperature=get_optional("temperature", api_obj, default_obj),
                max_tokens=get_optional("max_tokens", api_obj, default_obj, None),
                max_retries=0,
            )
        case "azure":
            # https://python.langchain.com/docs/integrations/chat/azure_chat_openai/
            default_obj = DEFAULT_VALUES["azure"]
            if "azure_ad_token" in api_obj:
                return AzureChatOpenAI(
                    azure_endpoint=get_mandatory("azure", "azure_endpoint", api_obj),
                    api_version=get_mandatory("azure", "api_version", api_obj),
                    azure_ad_token=get_mandatory("azure", "azure_ad_token", api_obj),
                    azure_deployment=get_optional(
                        "deployment_name", api_obj, default_obj
                    ),
                    model_version=get_optional("model_version", api_obj, default_obj),
                    model_name=get_optional("model_name", api_obj, default_obj),
                    temperature=get_optional("temperature", api_obj, default_obj),
                    openai_organization=get_optional(
                        "openai_organization", api_obj, default_obj
                    ),
                    max_tokens=get_optional("max_tokens", api_obj, default_obj, None),
                    max_retries=0,
                )
            return AzureChatOpenAI(
                azure_endpoint=get_mandatory("azure", "azure_endpoint", api_obj),
                api_version=get_mandatory("azure", "api_version", api_obj),
                api_key=get_mandatory("azure", "api_key", api_obj),
                azure_deployment=get_optional("deployment_name", api_obj, default_obj),
                model_version=get_optional("model_version", api_obj, default_obj),
                model_name=get_optional("model_name", api_obj, default_obj),
                temperature=get_optional("temperature", api_obj, default_obj),
                openai_organization=get_optional(
                    "openai_organization", api_obj, default_obj
                ),
                max_tokens=get_optional("max_tokens", api_obj, default_obj, None),
                max_retries=0,
            )
        case "openai":
            # https://python.langchain.com/docs/integrations/chat/openai/
            default_obj = DEFAULT_VALUES["openai"]
            return ChatOpenAI(
                api_key=get_mandatory("openai", "api_key", api_obj),
                model=get_optional("model", api_obj, default_obj),
                openai_organization=get_optional(
                    "openai_organization", api_obj, default_obj
                ),
                temperature=get_optional("temperature", api_obj, default_obj),
                frequency_penalty=get_optional(
                    "frequency_penalty", api_obj, default_obj
                ),
                presence_penalty=get_optional("presence_penalty", api_obj, default_obj),
                top_p=get_optional("top_p", api_obj, default_obj),
                max_tokens=get_optional("max_tokens", api_obj, default_obj, None),
                max_retries=0,
            )
        case "together":
            # https://python.langchain.com/docs/integrations/chat/together/
            default_obj = DEFAULT_VALUES["together"]
            return ChatTogether(
                api_key=get_mandatory("together", "api_key", api_obj),
                model=get_optional("model", api_obj, default_obj),
                temperature=get_optional("temperature", api_obj, default_obj),
                frequency_penalty=get_optional(
                    "frequency_penalty", api_obj, default_obj
                ),
                presence_penalty=get_optional("presence_penalty", api_obj, default_obj),
                top_p=get_optional("top_p", api_obj, default_obj),
                max_tokens=get_optional("max_tokens", api_obj, default_obj, None),
                timeout=None,  # TODO: Needed?
                max_retries=0,
            )
        # case "vertex": # NOT ALLOWED
        # https://python.langchain.com/docs/integrations/chat/google_vertex_ai_palm/
        case "google-genai":
            # https://python.langchain.com/docs/integrations/chat/google_generative_ai/
            default_obj = DEFAULT_VALUES["google-genai"]
            return ChatGoogleGenerativeAI(
                api_key=get_mandatory("google-genai", "api_key", api_obj),
                model=get_mandatory("google-genai", "model", api_obj),
                temperature=get_optional("temperature", api_obj, default_obj),
                top_p=get_optional("top_p", api_obj, default_obj),
                top_k=get_optional("top_k", api_obj, default_obj),
                max_tokens=get_optional("max_tokens", api_obj, default_obj, None),
                timeout=None,  # TODO: Needed?
                max_retries=0,
            )
        case "groq":
            # https://python.langchain.com/docs/integrations/chat/groq/
            default_obj = DEFAULT_VALUES["groq"]
            return ChatGroq(
                api_key=get_mandatory("groq", "api_key", api_obj),
                model=get_optional("model", api_obj, default_obj),
                temperature=get_optional("temperature", api_obj, default_obj),
                max_tokens=get_optional("max_tokens", api_obj, default_obj, None),
                timeout=None,  # TODO: Needed?
                max_retries=0,
            )
        case "cohere":
            # https://python.langchain.com/docs/integrations/chat/cohere/
            default_obj = DEFAULT_VALUES["cohere"]
            return ChatCohere(
                cohere_api_key=get_mandatory("cohere", "cohere_api_key", api_obj),
                model=get_optional("model", api_obj, default_obj),
                temperature=get_optional("temperature", api_obj, default_obj),
            )
        case "bedrock":
            # https://python.langchain.com/docs/integrations/chat/bedrock/
            default_obj = DEFAULT_VALUES["bedrock"]
            return ChatBedrock(
                model_id=get_mandatory("bedrock", "model_id", api_obj),
                region_name=get_mandatory("bedrock", "region_name", api_obj),
                aws_access_key_id=get_mandatory(
                    "bedrock", "aws_access_key_id", api_obj
                ),
                aws_secret_access_key=get_mandatory(
                    "bedrock", "aws_secret_access_key", api_obj
                ),
                aws_session_token=api_obj.get("aws_session_token"),  # Can be None
                endpoint_url=get_optional("endpoint_url", api_obj, default_obj),
                provider=get_optional("provider", api_obj, default_obj),
                model_kwargs=get_optional("model_kwargs", api_obj, default_obj),
                temperature=get_optional("temperature", api_obj, default_obj),
                max_tokens=get_optional("max_tokens", api_obj, default_obj, None),
            )
        case "bedrock-converse":
            # https://python.langchain.com/docs/integrations/chat/bedrock/#bedrock-converse-api
            default_obj = DEFAULT_VALUES["bedrock-converse"]
            return ChatBedrockConverse(
                model_id=get_mandatory("bedrock", "model_id", api_obj),
                region_name=get_mandatory("bedrock", "region_name", api_obj),
                aws_access_key_id=get_mandatory(
                    "bedrock", "aws_access_key_id", api_obj
                ),
                aws_secret_access_key=get_mandatory(
                    "bedrock", "aws_secret_access_key", api_obj
                ),
                aws_session_token=api_obj.get("aws_session_token"),  # Can be None
                endpoint_url=get_optional("endpoint_url", api_obj, default_obj),
                provider=get_optional("provider", api_obj, default_obj),
                temperature=get_optional("temperature", api_obj, default_obj),
                top_p=get_optional("top_p", api_obj, default_obj),
                max_tokens=get_optional("max_tokens", api_obj, default_obj, None),
            )
        case "huggingface":
            # https://python.langchain.com/docs/integrations/chat/huggingface/
            default_obj = DEFAULT_VALUES["huggingface"]
            llm: HuggingFaceEndpoint = None
            if "repo_id" in api_obj:
                llm = HuggingFaceEndpoint(
                    repo_id=get_mandatory("huggingface", "repo_id", api_obj),
                    huggingfacehub_api_token=api_obj.get(
                        "huggingfacehub_api_token"
                    ),  # can be None
                    task=get_optional("task", api_obj, default_obj, "text-generation"),
                    temperature=get_optional("temperature", api_obj, default_obj),
                    top_k=get_optional("top_k", api_obj, default_obj),
                    top_p=get_optional("top_p", api_obj, default_obj),
                    typical_p=get_optional("typical_p", api_obj, default_obj),
                    repetition_penalty=get_optional(
                        "repetition_penalty", api_obj, default_obj
                    ),
                    model_kwargs=get_optional("model_kwargs", api_obj, default_obj),
                    max_new_tokens=get_optional("max_tokens", api_obj, default_obj, -1),
                )
            elif "model" in api_obj:
                llm = HuggingFaceEndpoint(
                    model=get_mandatory("huggingface", "model", api_obj),
                    huggingfacehub_api_token=api_obj.get(
                        "huggingfacehub_api_token"
                    ),  # can be None
                    task=get_optional("task", api_obj, default_obj, "text-generation"),
                    temperature=get_optional("temperature", api_obj, default_obj),
                    top_k=get_optional("top_k", api_obj, default_obj),
                    top_p=get_optional("top_p", api_obj, default_obj),
                    typical_p=get_optional("typical_p", api_obj, default_obj),
                    repetition_penalty=get_optional(
                        "repetition_penalty", api_obj, default_obj
                    ),
                    model_kwargs=get_optional("model_kwargs", api_obj, default_obj),
                    max_new_tokens=get_optional("max_tokens", api_obj, default_obj, -1),
                )
            else:
                llm = HuggingFaceEndpoint(
                    endpoint_url=get_mandatory("huggingface", "endpoint_url", api_obj),
                    huggingfacehub_api_token=api_obj.get(
                        "huggingfacehub_api_token"
                    ),  # can be None
                    task=get_optional("task", api_obj, default_obj, "text-generation"),
                    temperature=get_optional("temperature", api_obj, default_obj),
                    top_k=get_optional("top_k", api_obj, default_obj),
                    top_p=get_optional("top_p", api_obj, default_obj),
                    typical_p=get_optional("typical_p", api_obj, default_obj),
                    repetition_penalty=get_optional(
                        "repetition_penalty", api_obj, default_obj
                    ),
                    model_kwargs=get_optional("model_kwargs", api_obj, default_obj),
                    max_new_tokens=get_optional("max_tokens", api_obj, default_obj, -1),
                )
            return ChatHuggingFace(llm=llm)
        case "nvidia":
            # https://python.langchain.com/docs/integrations/chat/nvidia_ai_endpoints/
            default_obj = DEFAULT_VALUES["nvidia"]
            has_key = "nvidia_api_key" in api_obj
            has_url = "base_url" in api_obj
            if not has_key and not has_url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either nvidia_api_key or base_url is a mandatory field for nvidia",
                )
            return ChatNVIDIA(
                nvidia_api_key=api_obj.get("nvidia_api_key"),  # Can be None
                base_url=api_obj.get("base_url"),  # Can be None
                model=get_optional("model", api_obj, default_obj),
                temperature=get_optional("temperature", api_obj, default_obj),
                top_p=get_optional("top_p", api_obj, default_obj),
                max_tokens=get_optional("max_tokens", api_obj, default_obj, None),
            )
        case "ai21":
            # https://python.langchain.com/docs/integrations/chat/ai21/
            default_obj = DEFAULT_VALUES["ai21"]
            return ChatAI21(
                api_key=get_mandatory("ai21", "api_key", api_obj),
                model=get_mandatory("ai21", "model", api_obj),
                temperature=get_optional("temperature", api_obj, default_obj),
                top_p=get_optional("top_p", api_obj, default_obj),
                max_tokens=get_optional("max_tokens", api_obj, default_obj, None),
            )
        case "upstage":
            # https://python.langchain.com/docs/integrations/chat/upstage/
            default_obj = DEFAULT_VALUES["upstage"]
            return ChatUpstage(
                api_key=get_mandatory("upstage", "api_key", api_obj),
                model=get_optional("model", api_obj, default_obj),
                temperature=get_optional("temperature", api_obj, default_obj),
                top_p=get_optional("top_p", api_obj, default_obj),
                max_tokens=get_optional("max_tokens", api_obj, default_obj, -1),
            )
        case "watsonx":
            # https://python.langchain.com/docs/integrations/chat/ibm_watsonx/
            default_obj = DEFAULT_VALUES["watsonx"]
            default_params = default_obj["params"]["type"][0]
            param_obj = get_optional("params", api_obj, default_obj) or {}
            if "model_id" not in api_obj and "deployment_id" not in api_obj:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either model_id or deployment_id is a mandatory field for watsonx",
                )
            if "project_id" not in api_obj and "space_id" not in api_obj:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either project_id or space_id is a mandatory field for watsonx",
                )
            params = (
                TextChatParameters(
                    frequency_penalty=get_optional(
                        "frequency_penalty", param_obj, default_params
                    ),
                    presence_penalty=get_optional(
                        "presence_penalty", param_obj, default_params
                    ),
                    temperature=get_optional("temperature", param_obj, default_params),
                    top_p=get_optional("top_p", param_obj, default_params),
                    max_tokens=get_optional(
                        "max_tokens", param_obj, default_params, None
                    ),
                    n=1,
                    logprobs=False,
                )
                if param_obj != {}
                else None
            )
            has_instance_id = "instance_id" in api_obj
            if has_instance_id and "token" in api_obj:
                return ChatWatsonx(
                    url=get_mandatory("watsonx", "url", api_obj),
                    instance_id=get_mandatory("watsonx", "instance_id", api_obj),
                    token=get_mandatory("watsonx", "token", api_obj),
                    model_id=api_obj.get("model_id"),  # Can be None
                    deployment_id=api_obj.get("deployment_id"),  # Can be None
                    project_id=api_obj.get("project_id"),  # Can be None
                    space_id=api_obj.get("space_id"),  # Can be None
                    version=get_optional("version", api_obj, default_obj),
                    params=params,
                )
            elif has_instance_id and "apikey" in api_obj:
                return ChatWatsonx(
                    url=get_mandatory("watsonx", "url", api_obj),
                    instance_id=get_mandatory("watsonx", "instance_id", api_obj),
                    apikey=get_mandatory("watsonx", "apikey", api_obj),
                    username=get_mandatory("watsonx", "username", api_obj),
                    model_id=api_obj.get("model_id"),  # Can be None
                    deployment_id=api_obj.get("deployment_id"),  # Can be None
                    project_id=api_obj.get("project_id"),  # Can be None
                    space_id=api_obj.get("space_id"),  # Can be None
                    version=get_optional("version", api_obj, default_obj),
                    params=params,
                )
            elif has_instance_id:
                return ChatWatsonx(
                    url=get_mandatory("watsonx", "url", api_obj),
                    instance_id=get_mandatory("watsonx", "instance_id", api_obj),
                    password=get_mandatory("watsonx", "password", api_obj),
                    username=get_mandatory("watsonx", "username", api_obj),
                    model_id=api_obj.get("model_id"),  # Can be None
                    deployment_id=api_obj.get("deployment_id"),  # Can be None
                    project_id=api_obj.get("project_id"),  # Can be None
                    space_id=api_obj.get("space_id"),  # Can be None
                    version=get_optional("version", api_obj, default_obj),
                    params=params,
                )
            return ChatWatsonx(
                url=get_mandatory("watsonx", "url", api_obj),
                apikey=get_mandatory("watsonx", "apikey", api_obj),
                model_id=api_obj.get("model_id"),  # Can be None
                deployment_id=api_obj.get("deployment_id"),  # Can be None
                project_id=api_obj.get("project_id"),  # Can be None
                space_id=api_obj.get("space_id"),  # Can be None
                version=get_optional("version", api_obj, default_obj),
                params=params,
            )
        case "snowflake":
            # https://python.langchain.com/docs/integrations/chat/snowflake/
            default_obj = DEFAULT_VALUES["snowflake"]
            return ChatSnowflakeCortex(
                snowflake_account=get_mandatory("snowflake", "account", api_obj),
                snowflake_username=get_mandatory("snowflake", "username", api_obj),
                snowflake_password=get_mandatory("snowflake", "password", api_obj),
                snowflake_database=get_mandatory("snowflake", "database", api_obj),
                snowflake_schema=get_mandatory("snowflake", "schema", api_obj),
                snowflake_role=get_mandatory("snowflake", "role", api_obj),
                snowflake_warehouse=get_mandatory("snowflake", "warehouse", api_obj),
                model=get_optional("model", api_obj, default_obj),
                cortex_function=get_optional("cortex_function", api_obj, default_obj),
                temperature=get_optional("temperature", api_obj, default_obj),
                top_p=get_optional("top_p", api_obj, default_obj),
                max_tokens=get_optional("max_tokens", api_obj, default_obj, None),
            )
        case "fragjetzt":
            if not FRAGJETZT_OLLAMA_ENDPOINT:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="FragJetzt Ollama endpoint is not available.",
                )
            # https://python.langchain.com/docs/integrations/chat/ollama/
            default_obj = DEFAULT_VALUES["fragjetzt"]
            num_ctx = min(
                8192, max(100, get_optional("max_tokens", api_obj, default_obj, 8192))
            )
            return ChatOllama(
                model="deepseek-r1:14b",
                num_ctx=num_ctx,
                endpoint=FRAGJETZT_OLLAMA_ENDPOINT,
                keep_alive="24h",
                # optional
                temperature=get_optional("temperature", api_obj, default_obj),
                repeat_penalty=get_optional("repeat_penalty", api_obj, default_obj),
                seed=get_optional("seed", api_obj, default_obj),
                top_k=get_optional("top_k", api_obj, default_obj),
                top_p=get_optional("top_p", api_obj, default_obj),
            )
        case _:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Something went wrong during provider selection.\nInvalid provider: "
                + config["provider"],
            )
