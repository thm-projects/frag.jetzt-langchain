from typing import Union
from uuid import UUID
from fastapi import APIRouter, Body, HTTPException, Request

from app.ai_conversation.api.models import (
    InputAPIModelInfo,
    InputAPISetup,
    InputApiSetupAllowedModel,
    InputApiSetupProviderSetting,
    InputProviderSetting,
    OutputAPIModelInfo,
    OutputAPISetup,
    OutputProviderSetting,
)
from app.ai_conversation.api.service import (
    create_api_model,
    create_api_setup,
    create_api_setup_allowed_model,
    create_api_setup_provider_setting,
    create_provider_setting,
    delete_api_model,
    delete_api_setup,
    delete_api_setup_allowed_model,
    delete_api_setup_provider_setting,
    delete_provider_setting,
    list_api_models,
    list_api_setup_allowed_models,
    list_api_setup_provider_settings,
    list_api_setups,
    list_provider_settings,
    patch_api_model,
    patch_api_setup,
    patch_provider_setting,
    create_api_model_admin,
    create_api_setup_admin,
    create_api_setup_allowed_model_admin,
    create_api_setup_provider_setting_admin,
    create_provider_setting_admin,
    delete_api_model_admin,
    delete_api_setup_admin,
    delete_api_setup_allowed_model_admin,
    delete_api_setup_provider_setting_admin,
    delete_provider_setting_admin,
    list_api_models_admin,
    list_api_setup_allowed_models_admin,
    list_api_setup_provider_settings_admin,
    list_api_setups_admin,
    list_provider_settings_admin,
    patch_api_model_admin,
    patch_api_setup_admin,
    patch_provider_setting_admin,
)
from app.routes.utils import REST_DATA
from app.security.oauth2 import DEPENDENCIES, per_req_config_modifier

router = APIRouter()


@router.get("/provider", dependencies=DEPENDENCIES)
async def list_providers() -> dict[str, dict[str, Union[dict, list]]]:
    return REST_DATA


@router.post("/provider-setting", dependencies=DEPENDENCIES, tags=["Provider Setting"])
async def create_setting(
    request: Request,
    provider_setting: InputProviderSetting = Body(..., embed=True),
) -> OutputProviderSetting:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await create_provider_setting(config, provider_setting)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/provider-setting", dependencies=DEPENDENCIES, tags=["Provider Setting"])
async def list_settings(request: Request) -> list[OutputProviderSetting]:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_provider_settings(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/provider-setting/{providerId}",
    dependencies=DEPENDENCIES,
    tags=["Provider Setting"],
)
async def update_setting(
    request: Request,
    providerId: UUID,
    provider_setting: dict = Body(..., embed=True),
) -> OutputProviderSetting:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await patch_provider_setting(config, providerId, provider_setting)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/provider-setting/{providerId}",
    dependencies=DEPENDENCIES,
    tags=["Provider Setting"],
)
async def delete_setting(
    request: Request,
    providerId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_provider_setting(config, providerId)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup", dependencies=DEPENDENCIES, tags=["API Setup"])
async def create_setup(
    request: Request,
    setup: InputAPISetup = Body(..., embed=True),
) -> OutputAPISetup:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await create_api_setup(config, setup)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/setup", dependencies=DEPENDENCIES, tags=["API Setup"])
async def list_setups(request: Request) -> list[OutputAPISetup]:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_api_setups(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/setup/{setupId}", dependencies=DEPENDENCIES, tags=["API Setup"])
async def update_setup(
    request: Request,
    setupId: UUID,
    setup: dict = Body(..., embed=True),
) -> OutputAPISetup:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await patch_api_setup(config, setupId, setup)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/setup/{setupId}", dependencies=DEPENDENCIES, tags=["API Setup"])
async def delete_setup(
    request: Request,
    setupId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_api_setup(config, setupId)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/setup/{setupId}/provider-setting/{providerId}",
    dependencies=DEPENDENCIES,
    tags=["API Setup - Provider Setting"],
)
async def create_setup_provider(
    request: Request,
    setupId: UUID,
    providerId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await create_api_setup_provider_setting(
            config,
            InputApiSetupProviderSetting(
                api_setup_id=setupId, api_provider_setting_id=providerId
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/setup/{setupId}/provider-setting/{providerId}",
    dependencies=DEPENDENCIES,
    tags=["API Setup - Provider Setting"],
)
async def delete_setup_provider(
    request: Request,
    setupId: UUID,
    providerId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_api_setup_provider_setting(config, setupId, providerId)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/setup/{setupId}/provider-setting",
    dependencies=DEPENDENCIES,
    tags=["API Setup - Provider Setting"],
)
async def list_setup_providers(
    request: Request,
    setupId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_api_setup_provider_settings(config, setupId)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/setup/{setupId}/allowed-model/{modelId}",
    dependencies=DEPENDENCIES,
    tags=["API Setup - Allowed Model"],
)
async def create_setup_model(
    request: Request,
    setupId: UUID,
    modelId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await create_api_setup_allowed_model(
            config,
            InputApiSetupAllowedModel(api_setup_id=setupId, api_model_info_id=modelId),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/setup/{setupId}/allowed-model/{modelId}",
    dependencies=DEPENDENCIES,
    tags=["API Setup - Allowed Model"],
)
async def delete_setup_model(
    request: Request,
    setupId: UUID,
    modelId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_api_setup_allowed_model(config, setupId, modelId)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/setup/{setupId}/allowed-model",
    dependencies=DEPENDENCIES,
    tags=["API Setup - Allowed Model"],
)
async def list_setup_models(
    request: Request,
    setupId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_api_setup_allowed_models(config, setupId)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model", dependencies=DEPENDENCIES, tags=["Model info"])
async def create_model(
    request: Request,
    model: InputAPIModelInfo = Body(..., embed=True),
) -> OutputAPIModelInfo:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await create_api_model(config, model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model", dependencies=DEPENDENCIES, tags=["Model info"])
async def list_models(request: Request) -> list[OutputAPIModelInfo]:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_api_models(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/model/{modelId}", dependencies=DEPENDENCIES, tags=["Model info"])
async def update_model(
    request: Request,
    modelId: UUID,
    model: dict = Body(..., embed=True),
) -> OutputAPIModelInfo:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await patch_api_model(config, modelId, model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/model/{modelId}", dependencies=DEPENDENCIES, tags=["Model info"])
async def delete_model(
    request: Request,
    modelId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_api_model(config, modelId)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/admin/provider-setting",
    dependencies=DEPENDENCIES,
    tags=["Provider Setting (Admin)"],
)
async def create_setting_admin(
    request: Request,
    provider_setting: InputProviderSetting = Body(..., embed=True),
) -> OutputProviderSetting:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await create_provider_setting_admin(config, provider_setting)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/admin/provider-setting",
    dependencies=DEPENDENCIES,
    tags=["Provider Setting (Admin)"],
)
async def list_settings_admin(request: Request) -> list[OutputProviderSetting]:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_provider_settings_admin(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/admin/provider-setting/{providerId}",
    dependencies=DEPENDENCIES,
    tags=["Provider Setting (Admin)"],
)
async def update_setting_admin(
    request: Request,
    providerId: UUID,
    provider_setting: dict = Body(..., embed=True),
) -> OutputProviderSetting:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await patch_provider_setting_admin(config, providerId, provider_setting)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/admin/provider-setting/{providerId}",
    dependencies=DEPENDENCIES,
    tags=["Provider Setting (Admin)"],
)
async def delete_setting_admin(
    request: Request,
    providerId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_provider_setting_admin(config, providerId)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/setup", dependencies=DEPENDENCIES, tags=["API Setup (Admin)"])
async def create_setup_admin(
    request: Request,
    setup: InputAPISetup = Body(..., embed=True),
) -> OutputAPISetup:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await create_api_setup_admin(config, setup)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/setup", dependencies=DEPENDENCIES, tags=["API Setup (Admin)"])
async def list_setups_admin(request: Request) -> list[OutputAPISetup]:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_api_setups_admin(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/admin/setup/{setupId}", dependencies=DEPENDENCIES, tags=["API Setup (Admin)"]
)
async def update_setup_admin(
    request: Request,
    setupId: UUID,
    setup: dict = Body(..., embed=True),
) -> OutputAPISetup:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await patch_api_setup_admin(config, setupId, setup)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/admin/setup/{setupId}", dependencies=DEPENDENCIES, tags=["API Setup (Admin)"]
)
async def delete_setup_admin(
    request: Request,
    setupId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_api_setup_admin(config, setupId)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/admin/setup/{setupId}/provider-setting/{providerId}",
    dependencies=DEPENDENCIES,
    tags=["API Setup - Provider Setting (Admin)"],
)
async def create_setup_provider_admin(
    request: Request,
    setupId: UUID,
    providerId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await create_api_setup_provider_setting_admin(
            config,
            InputApiSetupProviderSetting(
                api_setup_id=setupId, api_provider_setting_id=providerId
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/admin/setup/{setupId}/provider-setting/{providerId}",
    dependencies=DEPENDENCIES,
    tags=["API Setup - Provider Setting (Admin)"],
)
async def delete_setup_provider_admin(
    request: Request,
    setupId: UUID,
    providerId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_api_setup_provider_setting_admin(
            config, setupId, providerId
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/admin/setup/{setupId}/provider-setting",
    dependencies=DEPENDENCIES,
    tags=["API Setup - Provider Setting (Admin)"],
)
async def list_setup_providers_admin(
    request: Request,
    setupId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_api_setup_provider_settings_admin(config, setupId)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/admin/setup/{setupId}/allowed-model/{modelId}",
    dependencies=DEPENDENCIES,
    tags=["API Setup - Allowed Model (Admin)"],
)
async def create_setup_model_admin(
    request: Request,
    setupId: UUID,
    modelId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await create_api_setup_allowed_model_admin(
            config,
            InputApiSetupAllowedModel(api_setup_id=setupId, api_model_info_id=modelId),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/admin/setup/{setupId}/allowed-model/{modelId}",
    dependencies=DEPENDENCIES,
    tags=["API Setup - Allowed Model (Admin)"],
)
async def delete_setup_model_admin(
    request: Request,
    setupId: UUID,
    modelId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_api_setup_allowed_model_admin(config, setupId, modelId)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/admin/setup/{setupId}/allowed-model",
    dependencies=DEPENDENCIES,
    tags=["API Setup - Allowed Model (Admin)"],
)
async def list_setup_models_admin(
    request: Request,
    setupId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_api_setup_allowed_models_admin(config, setupId)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/model", dependencies=DEPENDENCIES, tags=["Model info (Admin)"])
async def create_model_admin(
    request: Request,
    model: InputAPIModelInfo = Body(..., embed=True),
) -> OutputAPIModelInfo:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await create_api_model_admin(config, model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/model", dependencies=DEPENDENCIES, tags=["Model info (Admin)"])
async def list_models_admin(request: Request) -> list[OutputAPIModelInfo]:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await list_api_models_admin(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/admin/model/{modelId}", dependencies=DEPENDENCIES, tags=["Model info (Admin)"]
)
async def update_model_admin(
    request: Request,
    modelId: UUID,
    model: dict = Body(..., embed=True),
) -> OutputAPIModelInfo:
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await patch_api_model_admin(config, modelId, model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/admin/model/{modelId}", dependencies=DEPENDENCIES, tags=["Model info (Admin)"]
)
async def delete_model_admin(
    request: Request,
    modelId: UUID,
):
    try:
        config = {"configurable": {}}
        await per_req_config_modifier(config, request)
        return await delete_api_model_admin(config, modelId)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
