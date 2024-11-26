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
  max_tokens INT NULL,
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

