-- Worker protocol: agent_capabilities, agent_assignments, job_runs, job_logs
-- Capability enum for typed worker capabilities
CREATE TYPE worker_capability AS ENUM (
    'filesystem',
    'email',
    'ocr',
    'image',
    'embed',
    'docproc'
);

-- agent_capabilities: normalized capability model
CREATE TABLE agent_capabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    capability worker_capability NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(agent_id, capability)
);

CREATE INDEX idx_agent_capabilities_agent ON agent_capabilities(agent_id);
CREATE INDEX idx_agent_capabilities_capability ON agent_capabilities(capability);

-- agent_assignments: source-to-worker assignment
CREATE TABLE agent_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(source_id)
);

CREATE INDEX idx_agent_assignments_agent ON agent_assignments(agent_id);
CREATE INDEX idx_agent_assignments_source ON agent_assignments(source_id);

-- job_runs: per-attempt tracking (for retries)
CREATE TYPE job_run_status AS ENUM ('running', 'completed', 'failed');

CREATE TABLE job_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    status job_run_status NOT NULL DEFAULT 'running',
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_job_runs_job ON job_runs(job_id);
CREATE INDEX idx_job_runs_agent ON job_runs(agent_id);
CREATE INDEX idx_job_runs_status ON job_runs(status);

-- job_logs: progress and error logs
CREATE TYPE job_log_level AS ENUM ('info', 'warn', 'error');

CREATE TABLE job_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    job_run_id UUID REFERENCES job_runs(id) ON DELETE SET NULL,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    level job_log_level NOT NULL DEFAULT 'info',
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_job_logs_job ON job_logs(job_id);
CREATE INDEX idx_job_logs_job_run ON job_logs(job_run_id);
CREATE INDEX idx_job_logs_created ON job_logs(created_at);

-- Retry control: central backoff managed by control plane
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS retry_count INT NOT NULL DEFAULT 0;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS max_retries INT NOT NULL DEFAULT 3;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMPTZ;

-- Worker auth: optional token for agent identification
ALTER TABLE agents ADD COLUMN IF NOT EXISTS agent_token TEXT;
