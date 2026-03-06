-- Web Content: Postgres + File Cache (Council vote #b875a756efe895d0)
-- Content stored in DB, materialized to disk on DMZ nodes by daemon

CREATE TABLE IF NOT EXISTS web_content (
    id SERIAL PRIMARY KEY,
    site VARCHAR(100) NOT NULL DEFAULT 'ganuda.us',
    path VARCHAR(500) NOT NULL,
    content_type VARCHAR(50) NOT NULL DEFAULT 'text/html',
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    metadata JSONB DEFAULT '{}',
    published BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'tpm'
);

-- Unique constraint: one content per site+path
CREATE UNIQUE INDEX IF NOT EXISTS idx_web_content_site_path
    ON web_content (site, path);

-- Index for materializer polling
CREATE INDEX IF NOT EXISTS idx_web_content_updated
    ON web_content (updated_at);

-- Index for published content only
CREATE INDEX IF NOT EXISTS idx_web_content_published
    ON web_content (site, published) WHERE published = true;

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_web_content_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.content_hash = encode(digest(NEW.content, 'sha256'), 'hex');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_web_content_updated ON web_content;
CREATE TRIGGER trg_web_content_updated
    BEFORE UPDATE ON web_content
    FOR EACH ROW
    EXECUTE FUNCTION update_web_content_timestamp();