-- App settings: key-value store for UI-configurable preferences.
-- Add settings permissions and link to admin
INSERT INTO permissions (id, name, description) VALUES
    (gen_random_uuid(), 'settings:read', 'View app settings'),
    (gen_random_uuid(), 'settings:write', 'Edit app settings')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT '00000000-0000-0000-0000-000000000001'::uuid, id FROM permissions WHERE name IN ('settings:read', 'settings:write')
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Replaces env-based config for operational settings.
CREATE TABLE IF NOT EXISTS app_settings (
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value_json TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (category, key)
);

-- Seed defaults (operational settings that were previously env-only)
INSERT INTO app_settings (category, key, value_json, updated_at) VALUES
    ('models', 'ollama_url', '"http://localhost:11434"', now()),
    ('models', 'embed_model', '"all-MiniLM-L6-v2"', now()),
    ('models', 'ask_model', '"llama3.2"', now()),
    ('internet_research', 'enabled', 'false', now()),
    ('document_processing', 'tika_endpoint', '"http://localhost:9998"', now()),
    ('document_processing', 'tika_timeout_secs', '60.0', now()),
    ('workers_jobs', 'max_retries', '3', now()),
    ('workers_jobs', 'retry_delay_secs', '60', now()),
    ('chat_memory', 'retention_days', '30', now()),
    ('chat_memory', 'context_limit', '10', now())
ON CONFLICT (category, key) DO NOTHING;
