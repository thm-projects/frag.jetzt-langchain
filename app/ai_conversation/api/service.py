import json
from typing import Tuple
from uuid import UUID
from app.ai_conversation.ai_conversation import get_connection_pool
from app.ai_conversation.api.models import (
    InputAPIModelInfo,
    InputAPISetup,
    InputApiSetupAllowedModel,
    InputApiSetupProviderSetting,
    InputProviderSetting,
    OutputAPIModelInfo,
    OutputAPISetup,
    OutputApiSetupAllowedModel,
    OutputApiSetupProviderSetting,
    OutputProviderSetting,
)
from app.routes.utils import REST_DATA


def _check_type(value: any, type_: str) -> bool:
    types = type_.split("|") if not isinstance(type_, list) else type_
    for t in types:
        if isinstance(t, dict):
            if not isinstance(value, dict):
                continue
            for k, v in t.items():
                if k not in value:
                    continue
                _check_type(value[k], v)
            return True
        elif t == "int":
            if isinstance(value, int):
                return True
        elif t == "str":
            if isinstance(value, str):
                return True
        elif t == "bool":
            if isinstance(value, bool):
                return True
        elif t == "float":
            if isinstance(value, float):
                return True
        elif t == "list":
            if isinstance(value, list):
                return True
        elif t == "dict":
            if isinstance(value, dict):
                return True
        elif t == "any":
            if value is not None:
                return True
        elif t == "null":
            if value is None:
                return True
    raise ValueError(f"Invalid type: {type_}")


def _verify_mandatory_fields(
    mandatory_description: list, data: dict, and_mode: bool, used_keys: set[str]
) -> Tuple[str, set[str]]:
    any_used = False
    for field in mandatory_description:
        if isinstance(field, dict):
            name = field["name"]
            if name not in data:
                if and_mode:
                    return f"Missing field: {name}", None
                else:
                    continue
            _check_type(data[name], field["type"])
            any_used = True
            used_keys.add(name)
            # or mode
            if not and_mode:
                break
            continue

        # field must be a list
        before = used_keys if and_mode else set(used_keys)
        error, used_keys = _verify_mandatory_fields(
            field, data, not and_mode, used_keys
        )
        if error:
            if and_mode:
                return error, None
            # else: revert
            used_keys = before
            continue
        any_used = True
        # or mode
        if not and_mode:
            break

    if not any_used:
        return "Mandatory fields error", None
    return "", used_keys


def _verify_provider_setting(provider_setting: InputProviderSetting) -> None:
    if provider_setting.provider not in REST_DATA:
        raise ValueError("Invalid provider")
    loaded = json.loads(provider_setting.json_settings)
    data = REST_DATA[provider_setting.provider]
    # mandatory fields
    error, used_keys = _verify_mandatory_fields(
        data["mandatory"],
        loaded,
        True,
        set(),
    )
    if error:
        raise ValueError(error)
    new_obj = {k: loaded[k] for k in used_keys}
    # optional fields
    for k, v in data["optional"].items():
        if k in loaded:
            _check_type(loaded[k], v)
            new_obj[k] = loaded[k]
    provider_setting.json_settings = json.dumps(new_obj)


async def create_provider_setting(
    config: dict, provider_setting: InputProviderSetting
) -> OutputProviderSetting:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetchrow(
            "INSERT INTO api_provider_setting(account_id, provider, json_settings, restriction_id) VALUES ($1, $2, $3, $4) RETURNING *;",
            account_id,
            provider_setting.provider,
            provider_setting.json_settings,
            provider_setting.restriction_id,
        )
        return OutputProviderSetting.load_from_db(data)


async def patch_provider_setting(
    config: dict, provider_setting: dict, provider_id: UUID
) -> OutputProviderSetting:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetchrow(
            "SELECT * FROM api_provider_setting WHERE id = $1 AND account_id = $2;",
            provider_id,
            account_id,
        )
        if not data:
            raise ValueError("Invalid provider settings id")
        if "provider" in provider_setting:
            if provider_setting["provider"] not in REST_DATA:
                raise ValueError("Invalid provider")
            data["provider"] = provider_setting["provider"]
        if "restriction_id" in provider_setting:
            data["restriction_id"] = provider_setting["restriction_id"]
        if "json_settings" in provider_setting:
            data["json_settings"] = provider_setting["json_settings"]
        obj = OutputProviderSetting.load_from_db(data)
        if "json_settings" in provider_setting:
            _verify_provider_setting(obj)
        data = conn.fetchrow(
            "UPDATE api_provider_setting SET provider = $1, json_settings = $2, restriction_id = $3 WHERE id = $4 RETURNING *;",
            obj.provider,
            obj.json_settings,
            obj.restriction_id,
            obj.id,
        )
        return OutputProviderSetting.load_from_db(data)


async def list_provider_settings(config: dict) -> list[OutputProviderSetting]:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetch(
            "SELECT * FROM api_provider_setting WHERE account_id = $1;", account_id
        )
        return [OutputProviderSetting.load_from_db(row) for row in data]


async def delete_provider_setting(config: dict, provider_id: UUID) -> None:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetchrow(
            "DELETE FROM api_provider_setting WHERE id = $1 AND account_id = $2 RETURNING *;",
            provider_id,
            account_id,
        )
        if not data:
            raise ValueError("Invalid provider settings id")


async def create_api_setup(config: dict, api_setup: InputAPISetup) -> OutputAPISetup:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetchrow(
            "INSERT INTO api_setup(account_id, restriction_id, only_allowed_models, pricing_strategy) VALUES ($1, $2, $3, $4) RETURNING *;",
            account_id,
            api_setup.restriction_id,
            api_setup.only_allowed_models,
            api_setup.pricing_strategy,
        )
        return OutputAPISetup.load_from_db(data)


async def list_api_setups(config: dict) -> list[OutputAPISetup]:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetch("SELECT * FROM api_setup WHERE account_id = $1;", account_id)
        return [OutputAPISetup.load_from_db(row) for row in data]


async def patch_api_setup(config: dict, setup: dict, setup_id: UUID) -> OutputAPISetup:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetchrow(
            "SELECT * FROM api_setup WHERE id = $1 AND account_id = $2;",
            setup_id,
            account_id,
        )
        if not data:
            raise ValueError("Invalid setup id")
        if "restriction_id" in setup:
            data["restriction_id"] = setup["restriction_id"]
        if "only_allowed_models" in setup:
            data["only_allowed_models"] = setup["only_allowed_models"]
        if "pricing_strategy" in setup:
            data["pricing_strategy"] = setup["pricing_strategy"]
        obj = OutputAPISetup.load_from_db(data)
        data = conn.fetchrow(
            "UPDATE api_setup SET restriction_id = $1, only_allowed_models = $2, pricing_strategy = $3 WHERE id = $4 RETURNING *;",
            obj.restriction_id,
            obj.only_allowed_models,
            obj.pricing_strategy,
            obj.id,
        )
        return OutputAPISetup.load_from_db(data)


async def delete_api_setup(config: dict, setup_id: UUID) -> None:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetchrow(
            "DELETE FROM api_setup WHERE id = $1 AND account_id = $2 RETURNING *;",
            setup_id,
            account_id,
        )
        if not data:
            raise ValueError("Invalid setup id")


async def create_api_setup_provider_setting(
    config: dict, api_setup_provider_setting: InputApiSetupProviderSetting
) -> OutputApiSetupProviderSetting:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetchrow(
            "SELECT id FROM api_setup WHERE id = $1 AND account_id = $2;",
            api_setup_provider_setting.api_setup_id,
            account_id,
        )
        if not data:
            raise ValueError("Invalid setup id")
        data = conn.fetchrow(
            "SELECT id FROM api_provider_setting WHERE id = $1 AND account_id = $2;",
            api_setup_provider_setting.api_provider_setting_id,
            account_id,
        )
        if not data:
            raise ValueError("Invalid provider settings id")
        data = conn.fetchrow(
            "INSERT INTO api_setup_provider(api_provider_setting_id, api_setup_id) VALUES ($1, $2) RETURNING *;",
            api_setup_provider_setting.api_provider_setting_id,
            api_setup_provider_setting.api_setup_id,
        )
        return OutputApiSetupProviderSetting.load_from_db(data)


async def list_api_setup_provider_settings(
    config: dict, setup_id: UUID
) -> list[OutputApiSetupProviderSetting]:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetchrow(
            "SELECT id FROM api_setup WHERE id = $1 AND account_id = $2;",
            setup_id,
            account_id,
        )
        if not data:
            raise ValueError("Invalid setup id")
        data = conn.fetch(
            "SELECT * FROM api_setup_provider WHERE api_setup_id = $1;",
            setup_id,
        )
        return [OutputApiSetupProviderSetting.load_from_db(row) for row in data]


async def delete_api_setup_provider_setting(
    config: dict, setup_id: UUID, provider_id: UUID
) -> None:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetchrow(
            "SELECT id FROM api_setup WHERE id = $1 AND account_id = $2;",
            setup_id,
            account_id,
        )
        if not data:
            raise ValueError("Invalid setup id")
        data = conn.fetchrow(
            "DELETE FROM api_setup_provider WHERE api_provider_setting_id = $1 AND api_setup_id = $2 RETURNING *;",
            provider_id,
            setup_id,
        )


async def create_api_setup_allowed_model(
    config: dict, input: InputApiSetupAllowedModel
) -> OutputApiSetupAllowedModel:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetchrow(
            "SELECT id FROM api_setup WHERE id = $1 AND account_id = $2;",
            input.api_setup_id,
            account_id,
        )
        if not data:
            raise ValueError("Invalid setup id")
        data = conn.fetchrow(
            "INSERT INTO api_setup_allowed_model(api_setup_id, api_model_info_id) VALUES ($1, $2) RETURNING *;",
            input.api_setup_id,
            input.api_model_info_id,
        )
        return OutputApiSetupAllowedModel.load_from_db(data)


async def list_api_setup_allowed_models(
    config: dict, setup_id: UUID
) -> list[OutputApiSetupAllowedModel]:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetchrow(
            "SELECT id FROM api_setup WHERE id = $1 AND account_id = $2;",
            setup_id,
            account_id,
        )
        if not data:
            raise ValueError("Invalid setup id")
        data = conn.fetch(
            "SELECT * FROM api_setup_allowed_model WHERE api_setup_id = $1;",
            setup_id,
        )
        return [OutputApiSetupAllowedModel.load_from_db(row) for row in data]


async def delete_api_setup_allowed_model(
    config: dict, setup_id: UUID, model_id: UUID
) -> None:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetchrow(
            "SELECT id FROM api_setup WHERE id = $1 AND account_id = $2;",
            setup_id,
            account_id,
        )
        if not data:
            raise ValueError("Invalid setup id")
        data = conn.fetchrow(
            "DELETE FROM api_setup_allowed_model WHERE api_model_info_id = $1 AND api_setup_id = $2 RETURNING *;",
            model_id,
            setup_id,
        )


async def create_api_model(config: dict, api_model_info: InputAPIModelInfo) -> OutputAPIModelInfo:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetchrow(
            "INSERT INTO api_model_info(account_id, model_name, provider, configurable_fields, input_token_cost, output_token_cost, max_tokens, max_context_length, currency) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING *;",
            account_id,
            api_model_info.model_name,
            api_model_info.provider,
            api_model_info.configurable_fields,
            api_model_info.input_token_cost,
            api_model_info.output_token_cost,
            api_model_info.max_tokens,
            api_model_info.max_context_length,
            api_model_info.currency,
        )
        return OutputAPIModelInfo.load_from_db(data)

async def patch_api_model(config: dict, api_model_info: dict) -> OutputAPIModelInfo:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetchrow(
            "SELECT * FROM api_model_info WHERE id = $1 AND account_id = $2;",
            api_model_info.id,
            account_id,
        )
        if not data:
            raise ValueError("Invalid model id")
        if "model_name" in api_model_info:
            data["model_name"] = api_model_info["model_name"]
        if "provider" in api_model_info:
            data["provider"] = api_model_info["provider"]
        if "configurable_fields" in api_model_info:
            data["configurable_fields"] = api_model_info["configurable_fields"]
        if "input_token_cost" in api_model_info:
            data["input_token_cost"] = api_model_info["input_token_cost"]
        if "output_token_cost" in api_model_info:
            data["output_token_cost"] = api_model_info["output_token_cost"]
        if "max_tokens" in api_model_info:
            data["max_tokens"] = api_model_info["max_tokens"]
        if "max_context_length" in api_model_info:
            data["max_context_length"] = api_model_info["max_context_length"]
        if "currency" in api_model_info:
            data["currency"] = api_model_info["currency"]
        obj = OutputAPIModelInfo.load_from_db(data)
        data = conn.fetchrow(
            "UPDATE api_model_info SET model_name = $1, provider = $2, configurable_fields = $3, input_token_cost = $4, output_token_cost = $5, max_tokens = $6, max_context_length = $7, currency = $8 WHERE id = $9 RETURNING *;",
            obj.model_name,
            obj.provider,
            obj.configurable_fields,
            obj.input_token_cost,
            obj.output_token_cost,
            obj.max_tokens,
            obj.max_context_length,
            obj.currency,
            obj.id,
        )
        return OutputAPIModelInfo.load_from_db(data)

async def list_api_models(config: dict) -> list[OutputAPIModelInfo]:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetch("SELECT * FROM api_model_info WHERE account_id = $1;", account_id)
        return [OutputAPIModelInfo.load_from_db(row) for row in data]

async def delete_api_model(config: dict, model_id: UUID) -> None:
    account_id = config["configurable"]["user_info"]["id"]
    async with get_connection_pool().acquire() as conn:
        data = conn.fetchrow(
            "DELETE FROM api_model_info WHERE id = $1 AND account_id = $2 RETURNING *;",
            model_id,
            account_id,
        )
        if not data:
            raise ValueError("Invalid model id")