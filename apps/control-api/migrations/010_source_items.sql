-- Source items: discovered units (e.g. files) from a source.
-- Connectors create these; downstream jobs reference them.
CREATE TABLE source_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    fingerprint TEXT NOT NULL,
    provenance JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(source_id, fingerprint)
);

CREATE INDEX idx_source_items_source ON source_items(source_id);
CREATE INDEX idx_source_items_fingerprint ON source_items(fingerprint);

-- Jobs may reference a source_item for downstream processing.
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source_item_id UUID REFERENCES source_items(id) ON DELETE SET NULL;
