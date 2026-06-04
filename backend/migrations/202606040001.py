SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION fn_generate_short_id(table_name TEXT)
RETURNS VARCHAR(7)
LANGUAGE plpgsql
AS $$
DECLARE
    generated_id VARCHAR(7);
    exists_id BOOLEAN;
BEGIN
    LOOP
        generated_id := LPAD(FLOOR(RANDOM() * 10000000)::TEXT, 7, '0');
        EXECUTE FORMAT('SELECT EXISTS (SELECT 1 FROM %I WHERE public_id = $1)', table_name)
        INTO exists_id
        USING generated_id;
        EXIT WHEN NOT exists_id;
    END LOOP;
    RETURN generated_id;
END;
$$;

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    public_id       VARCHAR(7) UNIQUE NOT NULL DEFAULT fn_generate_short_id('users'),
    email           VARCHAR(255) UNIQUE NOT NULL,
    name            VARCHAR(180) NOT NULL,
    password        TEXT NOT NULL,
    google_sub      TEXT UNIQUE,
    utm_attribution JSONB,
    is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
    created_by      UUID NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    modified_by     UUID NOT NULL,
    modified_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted         BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_users_email_deleted ON users (email, deleted);
CREATE INDEX idx_users_google_sub ON users (google_sub) WHERE google_sub IS NOT NULL;
CREATE INDEX idx_users_created_at ON users (created_at DESC);

CREATE TABLE role (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(80) UNIQUE NOT NULL,
    description TEXT,
    created_by  UUID NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    modified_by UUID NOT NULL,
    modified_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted     BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE user_role (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    role_id     UUID NOT NULL REFERENCES role (id) ON DELETE CASCADE,
    created_by  UUID NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    modified_by UUID NOT NULL,
    modified_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted     BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (user_id, role_id)
);

CREATE INDEX idx_user_role_user_id ON user_role (user_id) WHERE deleted = FALSE;
CREATE INDEX idx_user_role_role_id ON user_role (role_id) WHERE deleted = FALSE;

CREATE TABLE user_audit (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id            UUID NOT NULL,
    entity_id             UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    property_name         VARCHAR(120) NOT NULL,
    original_value_string TEXT,
    updated_value_string  TEXT,
    created_by            UUID NOT NULL,
    created_at            TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_audit_entity ON user_audit (entity_id, created_at DESC);

CREATE TABLE access_token (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    token       TEXT UNIQUE NOT NULL,
    valid_until TIMESTAMP,
    created_by  UUID NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    modified_by UUID NOT NULL,
    modified_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted     BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_access_token_lookup ON access_token (token) WHERE deleted = FALSE;
CREATE INDEX idx_access_token_user_created ON access_token (user_id, created_at DESC);

CREATE TABLE user_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    type        VARCHAR(40) NOT NULL,
    token_hash  BYTEA NOT NULL,
    context     JSONB NOT NULL DEFAULT '{}'::jsonb,
    expires_at  TIMESTAMP NOT NULL,
    used_at     TIMESTAMP,
    created_by  UUID NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    modified_by UUID NOT NULL,
    modified_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted     BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT ck_user_tokens_type CHECK (
        type IN ('email_verification', 'password_reset', 'social_link', 'account_deletion')
    )
);

CREATE INDEX idx_user_tokens_lookup ON user_tokens (type, token_hash);
CREATE INDEX idx_user_tokens_user_active ON user_tokens (user_id, type)
    WHERE used_at IS NULL AND deleted = FALSE;
CREATE UNIQUE INDEX ux_user_tokens_one_active ON user_tokens (user_id, type)
    WHERE used_at IS NULL AND deleted = FALSE;

CREATE TABLE system_announcement (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version    VARCHAR(64) NOT NULL,
    message    TEXT NOT NULL,
    start_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    end_at     TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_system_announcement_active ON system_announcement (start_at DESC, end_at);

CREATE TABLE email_log (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject           TEXT NOT NULL,
    sender            TEXT,
    recipients        TEXT[] NOT NULL,
    body              TEXT,
    status            VARCHAR(40) NOT NULL,
    provider          VARCHAR(80) NOT NULL,
    provider_response JSONB,
    error_message     TEXT,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_email_log_created_at ON email_log (created_at DESC);

CREATE TABLE contact_submissions (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name       VARCHAR(180) NOT NULL,
    email      VARCHAR(255) NOT NULL,
    mobile     VARCHAR(80),
    message    TEXT NOT NULL,
    page_url   TEXT,
    user_id    UUID REFERENCES users (id) ON DELETE SET NULL,
    user_plan  VARCHAR(120),
    plan_key   VARCHAR(120),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_contact_submissions_created_at ON contact_submissions (created_at DESC);

CREATE TABLE newsletter_subscriptions (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email                  VARCHAR(255) UNIQUE NOT NULL,
    name                   VARCHAR(180),
    source                 VARCHAR(120),
    page_url               TEXT,
    user_id                UUID REFERENCES users (id) ON DELETE SET NULL,
    user_plan              VARCHAR(120),
    ip_address             INET,
    user_agent             TEXT,
    confirmed_at           TIMESTAMP,
    unsubscribed_at        TIMESTAMP,
    unsubscribe_reason     TEXT,
    unsubscribe_token_hash TEXT NOT NULL,
    created_at             TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_newsletter_subscriptions_token ON newsletter_subscriptions (unsubscribe_token_hash);
CREATE INDEX idx_newsletter_subscriptions_active ON newsletter_subscriptions (email)
    WHERE unsubscribed_at IS NULL;

CREATE TABLE blocked_email_domains (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain      VARCHAR(255) UNIQUE NOT NULL,
    reason      TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_by  UUID,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    modified_by UUID,
    modified_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_blocked_email_domains_active ON blocked_email_domains (domain)
    WHERE is_active = TRUE;

CREATE TABLE registration_security_log (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type   VARCHAR(80) NOT NULL,
    email_domain VARCHAR(255),
    ip_address   INET,
    user_agent   TEXT,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_registration_security_log_ip_created ON registration_security_log (ip_address, created_at DESC);

CREATE TABLE traffic_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_hash         VARCHAR(64) NOT NULL,
    request_path    TEXT NOT NULL,
    http_method     VARCHAR(10) NOT NULL,
    status_code     INTEGER NOT NULL,
    response_bytes  INTEGER,
    referrer_domain VARCHAR(512),
    country_code    CHAR(2),
    device_category VARCHAR(20) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_traffic_log_created_at ON traffic_log (created_at DESC);
CREATE INDEX idx_traffic_log_path_created ON traffic_log (request_path, created_at DESC);

CREATE TABLE app_setting (
    key        TEXT PRIMARY KEY,
    value      JSONB NOT NULL,
    updated_by UUID,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

INSERT INTO users (
    id, public_id, email, name, password, is_verified, created_by, modified_by
) VALUES (
    '8d35b4fb-16f1-4d38-b592-580eaec56a99',
    '0000000',
    'no-reply@jarvis.local',
    'Jarvis System',
    '$2b$12$zE7hdziMP2I0V3TnniVk7u2KS6TohM6RyvuzHjYTbH7TzVRH6/kve',
    TRUE,
    '8d35b4fb-16f1-4d38-b592-580eaec56a99',
    '8d35b4fb-16f1-4d38-b592-580eaec56a99'
) ON CONFLICT (id) DO NOTHING;

ALTER TABLE users
    ADD CONSTRAINT fk_users_created_by FOREIGN KEY (created_by) REFERENCES users (id),
    ADD CONSTRAINT fk_users_modified_by FOREIGN KEY (modified_by) REFERENCES users (id);

ALTER TABLE role
    ADD CONSTRAINT fk_role_created_by FOREIGN KEY (created_by) REFERENCES users (id),
    ADD CONSTRAINT fk_role_modified_by FOREIGN KEY (modified_by) REFERENCES users (id);

ALTER TABLE user_role
    ADD CONSTRAINT fk_user_role_created_by FOREIGN KEY (created_by) REFERENCES users (id),
    ADD CONSTRAINT fk_user_role_modified_by FOREIGN KEY (modified_by) REFERENCES users (id);

ALTER TABLE user_audit
    ADD CONSTRAINT fk_user_audit_created_by FOREIGN KEY (created_by) REFERENCES users (id);

ALTER TABLE access_token
    ADD CONSTRAINT fk_access_token_created_by FOREIGN KEY (created_by) REFERENCES users (id),
    ADD CONSTRAINT fk_access_token_modified_by FOREIGN KEY (modified_by) REFERENCES users (id);

ALTER TABLE user_tokens
    ADD CONSTRAINT fk_user_tokens_created_by FOREIGN KEY (created_by) REFERENCES users (id),
    ADD CONSTRAINT fk_user_tokens_modified_by FOREIGN KEY (modified_by) REFERENCES users (id);

INSERT INTO role (name, description, created_by, modified_by)
VALUES
    ('admin', 'Can manage Jarvis users and settings.', '8d35b4fb-16f1-4d38-b592-580eaec56a99', '8d35b4fb-16f1-4d38-b592-580eaec56a99'),
    ('user', 'Standard Jarvis user.', '8d35b4fb-16f1-4d38-b592-580eaec56a99', '8d35b4fb-16f1-4d38-b592-580eaec56a99')
ON CONFLICT (name) DO NOTHING;

INSERT INTO user_role (user_id, role_id, created_by, modified_by)
SELECT
    '8d35b4fb-16f1-4d38-b592-580eaec56a99',
    role.id,
    '8d35b4fb-16f1-4d38-b592-580eaec56a99',
    '8d35b4fb-16f1-4d38-b592-580eaec56a99'
FROM role
WHERE role.name = 'admin'
ON CONFLICT (user_id, role_id) DO NOTHING;
"""


def upgrade(db):
    db.execute(SCHEMA_SQL)
