-- BEDROCK schema — minimal existence (PRIVACY.md)
-- No email, name, phone, or IP columns. Ever.

CREATE TABLE users (
  id TEXT PRIMARY KEY,
  created_day TEXT NOT NULL  -- YYYY-MM-DD only; no time
);

CREATE TABLE credentials (
  id TEXT PRIMARY KEY,                 -- base64url credential id
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  public_key BLOB NOT NULL,
  counter INTEGER NOT NULL DEFAULT 0,
  transports TEXT,                     -- JSON array or null
  created_day TEXT NOT NULL,
  UNIQUE(user_id, id)
);

CREATE INDEX idx_credentials_user ON credentials(user_id);

-- Opaque device rows; labels are client-encrypted ciphertext
CREATE TABLE devices (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  label_ct BLOB,                       -- encrypted label (nullable until set)
  label_iv BLOB,
  last_seen_day TEXT NOT NULL,
  created_day TEXT NOT NULL
);

CREATE INDEX idx_devices_user ON devices(user_id);

-- Refresh token families — hashed only; reuse of a rotated token = theft
CREATE TABLE refresh_tokens (
  id TEXT PRIMARY KEY,                 -- opaque token id
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  device_id TEXT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  family_id TEXT NOT NULL,             -- rotation family
  token_hash TEXT NOT NULL UNIQUE,     -- SHA-256 of raw refresh token
  expires_at INTEGER NOT NULL,         -- unix seconds
  revoked INTEGER NOT NULL DEFAULT 0,
  created_at INTEGER NOT NULL
);

CREATE INDEX idx_refresh_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_family ON refresh_tokens(family_id);

-- Versioned encrypted vault blobs (Tier-1 ciphertext only)
CREATE TABLE vault_versions (
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  ciphertext BLOB NOT NULL,
  iv BLOB NOT NULL,
  ct_hash TEXT NOT NULL,               -- hash of ciphertext (integrity / dedupe)
  created_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, version)
);

CREATE INDEX idx_vault_user_created ON vault_versions(user_id, created_at DESC);

-- Transient sealed security inbox — theft signals only; auto-expire 30 days
CREATE TABLE security_inbox (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,                  -- new_device | token_reuse | device_removed
  payload_ct BLOB NOT NULL,            -- sealed; server cannot usefully inspect
  payload_iv BLOB NOT NULL,
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);

CREATE INDEX idx_inbox_user ON security_inbox(user_id);
CREATE INDEX idx_inbox_expires ON security_inbox(expires_at);
