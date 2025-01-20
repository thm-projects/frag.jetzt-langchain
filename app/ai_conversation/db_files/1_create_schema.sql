CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE OR REPLACE FUNCTION trigger_timestamp_create_update_func()
    RETURNS trigger AS
$$
DECLARE
BEGIN
    IF (TG_OP = 'INSERT') THEN
        NEW.created_at = NOW();
        NEW.updated_at = NULL;
        RETURN NEW;
    ELSEIF (TG_OP = 'UPDATE') THEN
        IF (OLD.created_at <> NEW.created_at) THEN
            NEW.created_at = OLD.created_at;
        END IF;
        NEW.updated_at = NOW();
        RETURN NEW;
    ELSEIF (TG_OP = 'DELETE') THEN
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- file uploads

CREATE TABLE uploaded_file_content (
  id uuid NOT NULL DEFAULT uuid_generate_v1(),
  hash varchar(127) NOT NULL,
  file_ref uuid NOT NULL,
  unprocessed bool NOT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NULL,

  PRIMARY KEY (id),
  UNIQUE (hash),
  UNIQUE (file_ref)
);

CREATE TRIGGER trigger_timestamp_uploaded_file_content
    BEFORE INSERT OR UPDATE
    ON uploaded_file_content
    FOR EACH ROW
EXECUTE PROCEDURE trigger_timestamp_create_update_func();


CREATE TABLE uploaded_file (
  id uuid NOT NULL DEFAULT uuid_generate_v1(),
  content_id uuid NOT NULL,
  account_id uuid NOT NULL,
  name varchar(255) NOT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NULL,

  PRIMARY KEY (id),
  UNIQUE (content_id, account_id, name),
  FOREIGN KEY (content_id) REFERENCES uploaded_file_content(id) ON DELETE CASCADE,
  FOREIGN KEY (account_id) REFERENCES account(id) ON DELETE CASCADE
);

CREATE TRIGGER trigger_timestamp_uploaded_file
    BEFORE INSERT OR UPDATE
    ON uploaded_file
    FOR EACH ROW
EXECUTE PROCEDURE trigger_timestamp_create_update_func();

-- restrictions: quota_restrictions, time_restrictions, block_restrictions

CREATE TABLE restrictions (
  id uuid NOT NULL DEFAULT uuid_generate_v1(),
  account_id uuid NULL,
  room_id uuid NULL,
  administrated bool NOT NULL DEFAULT false,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (account_id) REFERENCES account(id) ON DELETE CASCADE,
  FOREIGN KEY (room_id) REFERENCES room(id) ON DELETE CASCADE
);

CREATE TRIGGER trigger_timestamp_restrictions
    BEFORE INSERT OR UPDATE
    ON restrictions
    FOR EACH ROW
EXECUTE PROCEDURE trigger_timestamp_create_update_func();

CREATE TYPE restriction_target AS ENUM (
  'ALL', 'UNREGISTERED', 'REGISTERED',
  'USER', 'UNREGISTERED_USER', 'REGISTERED_USER',
  'MOD', 'UNREGISTERED_MOD', 'REGISTERED_MOD', 
  'CREATOR'
);

CREATE TABLE block_restriction (
  id uuid NOT NULL DEFAULT uuid_generate_v1(),
  restriction_id uuid NOT NULL,
  target restriction_target NOT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NULL,

  PRIMARY KEY (id),
  UNIQUE (restriction_id, target),
  FOREIGN KEY (restriction_id) REFERENCES restrictions(id) ON DELETE CASCADE
);

CREATE TRIGGER trigger_timestamp_block_restriction
    BEFORE INSERT OR UPDATE
    ON block_restriction
    FOR EACH ROW
EXECUTE PROCEDURE trigger_timestamp_create_update_func();

CREATE TABLE quota_restriction (
  id uuid NOT NULL DEFAULT uuid_generate_v1(),
  restriction_id uuid NOT NULL,
  quota numeric(32, 16) NOT NULL,
  counter numeric(32, 16) NOT NULL DEFAULT 0,
  target restriction_target NOT NULL,
  reset_strategy varchar(32) NOT NULL,
  timezone varchar(32) NOT NULL,
  last_reset timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  end_time timestamp NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (restriction_id) REFERENCES restrictions(id) ON DELETE CASCADE
);

CREATE TRIGGER trigger_timestamp_quota_restriction
    BEFORE INSERT OR UPDATE
    ON quota_restriction
    FOR EACH ROW
EXECUTE PROCEDURE trigger_timestamp_create_update_func();

CREATE TABLE time_restriction (
  id uuid NOT NULL DEFAULT uuid_generate_v1(),
  restriction_id uuid NOT NULL,
  start_time timestamp NOT NULL,
  end_time timestamp NOT NULL,
  target restriction_target NOT NULL,
  repeat_strategy varchar(32) NOT NULL,
  timezone varchar(32) NOT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (restriction_id) REFERENCES restrictions(id) ON DELETE CASCADE
);

CREATE TRIGGER trigger_timestamp_time_restriction
    BEFORE INSERT OR UPDATE
    ON time_restriction
    FOR EACH ROW
EXECUTE PROCEDURE trigger_timestamp_create_update_func();

-- model info

CREATE TABLE api_model_info (
  id uuid NOT NULL DEFAULT uuid_generate_v1(),
  account_id uuid NULL,
  model_name varchar(255) NOT NULL,
  provider varchar(255) NOT NULL,
  configurable_fields text NOT NULL,
  input_token_cost numeric(32, 16) NOT NULL,
  output_token_cost numeric(32, 16) NOT NULL,
  currency varchar(32) NOT NULL DEFAULT 'USD',
  max_tokens INT NULL,
  max_context_length INT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (account_id) REFERENCES account(id) ON DELETE CASCADE
);

CREATE TRIGGER trigger_timestamp_api_model_info
    BEFORE INSERT OR UPDATE
    ON api_model_info
    FOR EACH ROW
EXECUTE PROCEDURE trigger_timestamp_create_update_func();

-- api provider settings

CREATE TABLE api_provider_setting (
  id uuid NOT NULL DEFAULT uuid_generate_v1(),
  account_id uuid NULL,
  provider varchar(255) NOT NULL,
  json_settings text NOT NULL,
  restriction_id uuid NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (account_id) REFERENCES account(id) ON DELETE CASCADE,
  FOREIGN KEY (restriction_id) REFERENCES restrictions(id) ON DELETE SET NULL
);

CREATE TRIGGER trigger_timestamp_api_provider_setting
    BEFORE INSERT OR UPDATE
    ON api_provider_setting
    FOR EACH ROW
EXECUTE PROCEDURE trigger_timestamp_create_update_func();

-- api setup, allowed models and providers

CREATE TABLE api_setup (
  id uuid NOT NULL DEFAULT uuid_generate_v1(),
  account_id uuid NULL,
  restriction_id uuid NULL,
  only_allowed_models bool NOT NULL DEFAULT false,
  pricing_strategy varchar(255) NOT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (account_id) REFERENCES account(id) ON DELETE CASCADE,
  FOREIGN KEY (restriction_id) REFERENCES restrictions(id) ON DELETE SET NULL
);

CREATE TRIGGER trigger_timestamp_api_setup
    BEFORE INSERT OR UPDATE
    ON api_setup
    FOR EACH ROW
EXECUTE PROCEDURE trigger_timestamp_create_update_func();

CREATE TABLE api_setup_provider (
  id uuid NOT NULL DEFAULT uuid_generate_v1(),
  api_setup_id uuid NOT NULL,
  api_provider_setting_id uuid NOT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE (api_setup_id, api_provider_setting_id),
  FOREIGN KEY (api_setup_id) REFERENCES api_setup(id) ON DELETE CASCADE,
  FOREIGN KEY (api_provider_setting_id) REFERENCES api_provider_setting(id) ON DELETE CASCADE
);

CREATE TABLE api_setup_allowed_model (
  id uuid NOT NULL DEFAULT uuid_generate_v1(),
  api_setup_id uuid NOT NULL,
  api_model_info_id uuid NOT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE (api_setup_id, api_model_info_id),
  FOREIGN KEY (api_setup_id) REFERENCES api_setup(id) ON DELETE CASCADE,
  FOREIGN KEY (api_model_info_id) REFERENCES api_model_info(id) ON DELETE CASCADE
);

-- api voucher

CREATE TABLE api_voucher (
  id uuid NOT NULL DEFAULT uuid_generate_v1(),
  room_id uuid NULL,
  voucher varchar(64) NOT NULL,
  restriction_id uuid NOT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (room_id) REFERENCES room(id) ON DELETE SET NULL,
  FOREIGN KEY (restriction_id) REFERENCES restrictions(id) ON DELETE CASCADE
);


CREATE TRIGGER trigger_timestamp_api_voucher
    BEFORE INSERT OR UPDATE
    ON api_voucher
    FOR EACH ROW
EXECUTE PROCEDURE trigger_timestamp_create_update_func();

-- room restrictions: api setup, restrictions, voucher

CREATE TABLE room_ai_setting (
  id uuid NOT NULL DEFAULT uuid_generate_v1(),
  room_id uuid NOT NULL,
  restriction_id uuid NULL,
  api_setup_id uuid NULL,
  api_voucher_id uuid NULL,
  allow_global_assistants bool NOT NULL DEFAULT true,
  allow_user_assistants bool NOT NULL DEFAULT false,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NULL,

  PRIMARY KEY (id),
  UNIQUE (room_id, restriction_id),
  FOREIGN KEY (room_id) REFERENCES room(id) ON DELETE CASCADE,
  FOREIGN KEY (restriction_id) REFERENCES restrictions(id) ON DELETE SET NULL,
  FOREIGN KEY (api_setup_id) REFERENCES api_setup(id) ON DELETE SET NULL,
  FOREIGN KEY (api_voucher_id) REFERENCES api_voucher(id) ON DELETE SET NULL
);

CREATE TRIGGER trigger_timestamp_room_ai_setting
    BEFORE INSERT OR UPDATE
    ON room_ai_setting
    FOR EACH ROW
EXECUTE PROCEDURE trigger_timestamp_create_update_func();

-- assistant: todo: files, tools!

CREATE TYPE assistant_share AS ENUM ('MINIMAL', 'VIEWABLE', 'COPYABLE');

CREATE TABLE assistant (
  id uuid NOT NULL DEFAULT uuid_generate_v1(),
  room_id uuid NULL,
  account_id uuid NULL,
  name varchar(256) NOT NULL,
  description varchar(4096) NOT NULL,
  instruction text NOT NULL,
  override_json_settings text NOT NULL,
  model_name varchar(256) NOT NULL,
  provider_list varchar(1024) NULL,
  share_type assistant_share NOT NULL DEFAULT 'MINIMAL',
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (room_id) REFERENCES room(id) ON DELETE CASCADE,
  FOREIGN KEY (account_id) REFERENCES account(id) ON DELETE CASCADE
);

CREATE TRIGGER trigger_timestamp_assistant
    BEFORE INSERT OR UPDATE
    ON assistant
    FOR EACH ROW
EXECUTE PROCEDURE trigger_timestamp_create_update_func();

CREATE TABLE assistant_file (
  assistant_id uuid NOT NULL,
  uploaded_file_id uuid NOT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (assistant_id, uploaded_file_id),
  FOREIGN KEY (assistant_id) REFERENCES assistant(id) ON DELETE CASCADE,
  FOREIGN KEY (uploaded_file_id) REFERENCES uploaded_file(id) ON DELETE CASCADE
);

-- threads

CREATE TYPE thread_share AS ENUM ('NONE', 'CHAT_VIEW', 'CHAT_COPY', 'THREAD_VIEW', 'THREAD_COPY', 'SYNC_VIEW', 'SYNC_COPY');

CREATE TABLE thread (
  id uuid NOT NULL DEFAULT uuid_generate_v1(),
  room_id uuid NULL,
  account_id uuid NOT NULL,
  name varchar(255) NOT NULL,
  share_type thread_share NOT NULL DEFAULT 'NONE',
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (room_id) REFERENCES room(id) ON DELETE CASCADE,
  FOREIGN KEY (account_id) REFERENCES account(id) ON DELETE CASCADE
);



-- DATA

INSERT INTO api_model_info(model_name, provider, configurable_fields, input_token_cost, output_token_cost, max_tokens, max_context_length, currency)
VALUES ('gpt-4o', 'openai', '["openai_organization","temperature","frequency_penalty","presence_penalty","top_p"]', 2.5e-6, 10e-6, 16384, 128000, 'USD'),
       ('gpt-4o-2024-11-20', 'openai', '["openai_organization","temperature","frequency_penalty","presence_penalty","top_p"]', 2.5e-6, 10e-6, 16384, 128000, 'USD'),
       ('gpt-4o-mini', 'openai', '["openai_organization","temperature","frequency_penalty","presence_penalty","top_p"]', 0.15e-6, 0.6e-6, 16384, 128000, 'USD'),
       ('claude-3-5-sonnet-20241022', 'anthropic', '["temperature","top_k","top_p","max_tokens"]', 3e-6, 15e-6, 8192, 200000, 'USD'),
       ('claude-3-5-haiku-20241022', 'anthropic', '["temperature","top_k","top_p","max_tokens"]', 1e-6, 5e-6, 8192, 200000, 'USD'),
       ('mistral-large-latest', 'mistral', '["temperature","top_p"]', 2e-6, 6e-6, NULL, 128000, 'USD'),
       ('pixtral-large-latest', 'mistral', '["temperature","top_p"]', 2e-6, 6e-6, NULL, 128000, 'USD'),
       ('ministral-8b-latest', 'mistral', '["temperature","top_p"]', 0.1e-6, 0.1e-6, NULL, 128000, 'USD'),
       ('ministral-3b-latest', 'mistral', '["temperature","top_p"]', 0.04e-6, 0.04e-6, NULL, 128000, 'USD'),
       ('mistral-small-latest', 'mistral', '["temperature","top_p"]', 0.2e-6, 0.6e-6, NULL, 32000, 'USD'),
       ('codestral-latest', 'mistral', '["temperature","top_p"]', 0.2e-6, 0.6e-6, NULL, 32000, 'USD'),
       ('accounts/fireworks/models/llama-v3p1-405b-instruct', 'fireworks', '["temperature"]', 3e-6, 3e-6, NULL, 131072, 'USD'),
       ('accounts/fireworks/models/llama-v3p1-70b-instruct', 'fireworks', '["temperature"]', 0.9e-6, 0.9e-6, NULL, 131072, 'USD'),
       ('accounts/fireworks/models/llama-v3p1-8b-instruct', 'fireworks', '["temperature"]', 0.2e-6, 0.2e-6, NULL, 131072, 'USD'),
       ('accounts/fireworks/models/llama-v3p2-3b-instruct', 'fireworks', '["temperature"]', 0.2e-6, 0.2e-6, NULL, 131072, 'USD'),
       ('accounts/fireworks/models/qwen2p5-coder-32b-instruct', 'fireworks', '["temperature"]', 0.9e-6, 0.9e-6, NULL, 32768, 'USD'),
       ('accounts/fireworks/models/mixtral-8x22b-instruct', 'fireworks', '["temperature"]', 0.9e-6, 0.9e-6, NULL, 65536, 'USD'),
       ('accounts/fireworks/models/llama-v3p2-11b-vision-instruct', 'fireworks', '["temperature"]', 0.2e-6, 0.2e-6, NULL, 131072, 'USD'),
       ('accounts/fireworks/models/mixtral-8x7b-instruct-hf', 'fireworks', '["temperature"]', 0.5e-6, 0.5e-6, NULL, 32768, 'USD'),
       ('accounts/fireworks/models/yi-large', 'fireworks', '["temperature"]', 3e-6, 3e-6, NULL, 32768, 'USD'),
       ('accounts/fireworks/models/llama-v3-70b-instruct-hf', 'fireworks', '["temperature"]', 0.9e-6, 0.9e-6, NULL, 8192, 'USD'),
       ('accounts/fireworks/models/qwen2p5-72b-instruct', 'fireworks', '["temperature"]', 0.9e-6, 0.9e-6, NULL, 32768, 'USD'),
       ('accounts/fireworks/models/llama-v3-8b-instruct', 'fireworks', '["temperature"]', 0.2e-6, 0.2e-6, NULL, 8192, 'USD'),
       ('accounts/fireworks/models/llama-v3-70b-instruct', 'fireworks', '["temperature"]', 0.9e-6, 0.9e-6, NULL, 8192, 'USD'),
       ('accounts/fireworks/models/starcoder-7b', 'fireworks', '["temperature"]', 0.2e-6, 0.2e-6, NULL, 8192, 'USD'),
       ('accounts/fireworks/models/gemma2-9b-it', 'fireworks', '["temperature"]', 0.2e-6, 0.2e-6, NULL, 8192, 'USD'),
       ('accounts/fireworks/models/qwen-qwq-32b-preview', 'fireworks', '["temperature"]', 0.9e-6, 0.9e-6, NULL, 32768, 'USD'),
       ('accounts/fireworks/models/llama-v3-8b-instruct-hf', 'fireworks', '["temperature"]', 0.2e-6, 0.2e-6, NULL, 8192, 'USD'),
       ('accounts/fireworks/models/llama-v3p2-1b-instruct', 'fireworks', '["temperature"]', 0.2e-6, 0.2e-6, NULL, 131072, 'USD'),
       ('accounts/fireworks/models/llama-v3p1-405b-instruct-long', 'fireworks', '["temperature"]', 3e-6, 3e-6, NULL, 131072, 'USD'),
       ('accounts/fireworks/models/firefunction-v2', 'fireworks', '["temperature"]', 0.9e-6, 0.9e-6, NULL, 8192, 'USD'),
       ('accounts/fireworks/models/phi-3-vision-128k-instruct', 'fireworks', '["temperature"]', 0.2e-6, 0.2e-6, NULL, 128000, 'USD'),
       ('accounts/fireworks/models/llama-v3p2-90b-vision-instruct', 'fireworks', '["temperature"]', 0.9e-6, 0.9e-6, NULL, 131072, 'USD'),
       ('accounts/fireworks/models/mixtral-8x7b-instruct', 'fireworks', '["temperature"]', 0.5e-6, 0.5e-6, NULL, 32768, 'USD'),
       ('accounts/fireworks/models/mythomax-l2-13b', 'fireworks', '["temperature"]', 0.2e-6, 0.2e-6, NULL, 4096, 'USD'),
       ('accounts/fireworks/models/starcoder-16b', 'fireworks', '["temperature"]', 0.2e-6, 0.2e-6, NULL, 8192, 'USD'),
       ('accounts/fireworks/models/firefunction-v1', 'fireworks', '["temperature"]', 0.5e-6, 0.5e-6, NULL, 32768, 'USD'),
       ('gemini-1.5-flash-001', 'google-genai', '["temperature","top_p","top_k"]', 0.01875e-6, 0.075e-6, NULL, 128000, 'USD'),
       ('gemini-1.5-pro-001', 'google-genai', '["temperature","top_p","top_k"]', 0.3125e-6, 1.25e-6, NULL, 128000, 'USD'),
       ('gemma2-9b-it', 'groq', '["temperature"]', 0.2e-6, 0.2e-6, NULL, 8192, 'USD'),
       ('gemma-7b-it', 'groq', '["temperature"]', 0.07e-6, 0.07e-6, NULL, 8192, 'USD'),
       ('llama3-groq-70b-8192-tool-use-preview', 'groq', '["temperature"]', 0.89e-6, 0.89e-6, NULL, 8192, 'USD'),
       ('llama3-groq-8b-8192-tool-use-preview', 'groq', '["temperature"]', 0.19e-6, 0.19e-6, NULL, 8192, 'USD'),
       ('llama-3.1-70b-versatile', 'groq', '["temperature"]', 0.59e-6, 0.79e-6, 32768, 128000, 'USD'),
       ('llama-3.1-8b-instant', 'groq', '["temperature"]', 0.05e-6, 0.08e-6, 8192, 128000, 'USD'),
       ('llama-3.2-1b-preview', 'groq', '["temperature"]', 0.04e-6, 0.04e-6, 8192, 128000, 'USD'),
       ('llama-3.2-3b-preview', 'groq', '["temperature"]', 0.06e-6, 0.06e-6, 8192, 128000, 'USD'),
       ('llama-3.2-11b-vision-preview', 'groq', '["temperature"]', 0.18e-6, 0.18e-6, 8192, 128000, 'USD'),
       ('llama-3.2-90b-vision-preview', 'groq', '["temperature"]', 0.9e-6, 0.9e-6, 8192, 128000, 'USD'),
       ('llama3-70b-8192', 'groq', '["temperature"]', 0.59e-6, 0.79e-6, NULL, 8192, 'USD'),
       ('llama3-8b-8192', 'groq', '["temperature"]', 0.05e-6, 0.08e-6, NULL, 8192, 'USD'),
       ('mixtral-8x7b-32768', 'groq', '["temperature"]', 0.24e-6, 0.24e-6, NULL, 32768, 'USD'),
       ('command-r-plus-08-2024', 'cohere', '["temperature"]', 2.5e-6, 10e-6, 4000, 128000, 'USD'),
       ('command-r-plus', 'cohere', '["temperature"]', 2.5e-6, 10e-6, 4000, 128000, 'USD'),
       ('command-r-08-2024', 'cohere', '["temperature"]', 0.15e-6, 0.6e-6, 4000, 128000, 'USD'),
       ('command-r', 'cohere', '["temperature"]', 0.15e-6, 0.6e-6, 4000, 128000, 'USD'),
       ('jamba-1.5-mini', 'ai21', '["temperature","top_p"]', 0.2e-6, 0.4e-6, NULL, 256000, 'USD'),
       ('jamba-1.5-large', 'ai21', '["temperature","top_p"]', 2e-6, 8e-6, NULL, 256000, 'USD'),
       ('solar-pro', 'upstage', '["temperature","top_p"]', 0.25e-6, 0.25e-6, NULL, 32768, 'USD'),
       ('solar-mini', 'upstage', '["temperature","top_p"]', 0.15e-6, 0.15e-6, NULL, 32768, 'USD'),
       ('solar-mini-ja', 'upstage', '["temperature","top_p"]', 0.15e-6, 0.15e-6, NULL, 32768, 'USD'),
       ('granite-13b-chat', 'watsonx', '["params","version"]', 0.6e-6, 0.6e-6, NULL, 8192, 'USD'),
       ('granite-13b-instruct', 'watsonx', '["params","version"]', 0.6e-6, 0.6e-6, NULL, 8192, 'USD'),
       ('granite-20b-multilingual', 'watsonx', '["params","version"]', 0.6e-6, 0.6e-6, NULL, 8190, 'USD'),
       ('llama-2-70b-chat', 'watsonx', '["params","version"]', 1.8e-6, 1.8e-6, NULL, 4096, 'USD'),
       ('llama-2-13b-chat', 'watsonx', '["params","version"]', 0.6e-6, 0.6e-6, NULL, 4096, 'USD'),
       ('codellama-34b-instruct', 'watsonx', '["params","version"]', 1.8e-6, 1.8e-6, NULL, 4096, 'USD'),
       ('mixtral-8x7b-instruct', 'watsonx', '["params","version"]', 0.6e-6, 0.6e-6, NULL, 32768, 'USD'),
       ('granite-8b-japanese', 'watsonx', '["params","version"]', 0.6e-6, 0.6e-6, NULL, 4096, 'USD'),
       ('flan-t5-xl-3b', 'watsonx', '["params","version"]', 0.6e-6, 0.6e-6, NULL, 4096, 'USD'),
       ('flan-t5-xxl-11b', 'watsonx', '["params","version"]', 1.8e-6, 1.8e-6, NULL, 4096, 'USD'),
       ('flan-ul2-20b', 'watsonx', '["params","version"]', 5e-6, 5e-6, NULL, 4096, 'USD'),
       ('elyza-japanese-llama-2-7b-instruct', 'watsonx', '["params","version"]', 1.8e-6, 1.8e-6, NULL, 4096, 'USD'),
       ('mt0-xxl-13b', 'watsonx', '["params","version"]', 1.8e-6, 1.8e-6, NULL, 4096, 'USD');