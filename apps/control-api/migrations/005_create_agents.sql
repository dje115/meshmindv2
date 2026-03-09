-- Agents (workers that claim jobs)
CREATE TYPE agent_status AS ENUM ('active', 'stale', 'dead');

CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    capabilities TEXT[] NOT NULL DEFAULT '{}',
    status agent_status NOT NULL DEFAULT 'active',
    last_heartbeat TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_last_heartbeat ON agents(last_heartbeat);
