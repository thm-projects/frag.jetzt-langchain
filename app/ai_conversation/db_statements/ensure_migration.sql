CREATE TABLE IF NOT EXISTS migration (
  version int NOT NULL,
  hash varchar(255) NOT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (version)
);