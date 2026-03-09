-- Seed permissions, admin role, default workspace
-- Dev admin user is created by application when MESHMIND_SEED_DEV_ADMIN=true

INSERT INTO permissions (id, name, description) VALUES
    (gen_random_uuid(), 'search:read', 'Run search'),
    (gen_random_uuid(), 'ask:read', 'Run Ask'),
    (gen_random_uuid(), 'sources:read', 'List/view sources'),
    (gen_random_uuid(), 'sources:write', 'Create/update/delete sources'),
    (gen_random_uuid(), 'sources:ingest', 'Trigger ingest'),
    (gen_random_uuid(), 'jobs:read', 'List jobs'),
    (gen_random_uuid(), 'admin:users', 'Manage users'),
    (gen_random_uuid(), 'admin:roles', 'Manage roles'),
    (gen_random_uuid(), 'admin:workers', 'View workers')
ON CONFLICT (name) DO NOTHING;

INSERT INTO roles (id, name, description) VALUES
    ('00000000-0000-0000-0000-000000000001', 'admin', 'Full admin access')
ON CONFLICT (name) DO NOTHING;

-- Link admin role to all permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT '00000000-0000-0000-0000-000000000001'::uuid, id FROM permissions
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO workspaces (id, name, slug, description) VALUES
    ('00000000-0000-0000-0000-000000000002', 'Default', 'default', 'Default workspace')
ON CONFLICT (slug) DO NOTHING;
