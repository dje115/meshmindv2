-- Data sources
CREATE TYPE source_kind AS ENUM ('filesystem', 'sqlite', 'csv', 'json');
CREATE TYPE source_status AS ENUM ('pending', 'approved', 'ingesting', 'completed', 'failed');

CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    kind source_kind NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    status source_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sources_workspace ON sources(workspace_id);
CREATE INDEX idx_sources_status ON sources(status);
