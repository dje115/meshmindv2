-- Chunk index for keyword/vector hybrid search.
-- Populated by embed worker via index-chunks endpoint.
CREATE TABLE chunk_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_item_id UUID NOT NULL REFERENCES source_items(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    chunk_id TEXT NOT NULL,
    chunk_index INT NOT NULL,
    text TEXT NOT NULL,
    page_index INT,
    sheet_index INT,
    sheet_name TEXT,
    provenance JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(source_item_id, chunk_id)
);

CREATE INDEX idx_chunk_index_workspace ON chunk_index(workspace_id);
CREATE INDEX idx_chunk_index_source ON chunk_index(source_id);
CREATE INDEX idx_chunk_index_source_item ON chunk_index(source_item_id);

-- Full-text search on chunk text
ALTER TABLE chunk_index ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (to_tsvector('english', coalesce(text, ''))) STORED;
CREATE INDEX idx_chunk_index_search ON chunk_index USING GIN(search_vector);
