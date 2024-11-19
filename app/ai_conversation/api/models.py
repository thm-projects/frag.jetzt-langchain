from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.ai_conversation.db_decorator import entity


@dataclass
class InputProviderSetting:
    provider: str
    json_settings: str
    restriction_id: Optional[UUID]


@entity
@dataclass
class OutputProviderSetting:
    id: UUID
    account_id: UUID
    provider: str
    json_settings: str
    restriction_id: UUID
    created_at: datetime
    updated_at: datetime


@dataclass
class InputAPISetup:
    restriction_id: Optional[UUID]
    only_allowed_models: bool
    pricing_strategy: str


@entity
@dataclass
class OutputAPISetup:
    id: UUID
    account_id: UUID
    restriction_id: UUID
    only_allowed_models: bool
    pricing_strategy: str
    created_at: datetime
    updated_at: datetime


@dataclass
class InputApiSetupProviderSetting:
    api_provider_setting_id: UUID
    api_setup_id: UUID


@entity
@dataclass
class OutputApiSetupProviderSetting:
    id: UUID
    api_provider_setting_id: UUID
    api_setup_id: UUID
    created_at: datetime


@dataclass
class InputApiSetupAllowedModel:
    api_setup_id: UUID
    api_model_info_id: UUID


@entity
@dataclass
class OutputApiSetupAllowedModel:
    id: UUID
    api_setup_id: UUID
    api_model_info_id: UUID
    created_at: datetime


@dataclass
class InputAPIModelInfo:
    model_name: str
    provider: str
    configurable_fields: str
    input_token_cost: Decimal
    output_token_cost: Decimal
    max_tokens: Optional[int]

@entity
@dataclass
class OutputAPIModelInfo:
    id: UUID
    account_id: UUID
    model_name: str
    provider: str
    configurable_fields: str
    input_token_cost: Decimal
    output_token_cost: Decimal
    max_tokens: Optional[int]
    created_at: datetime
    updated_at: datetime