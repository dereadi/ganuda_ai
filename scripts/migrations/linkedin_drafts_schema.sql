-- LinkedIn post draft approval queue for Deer
CREATE TABLE IF NOT EXISTS linkedin_drafts (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,  -- email_scout, thermal_insight, manual
    source_ref TEXT,  -- email id, thermal hash, or free text
    draft_content TEXT NOT NULL,
    hashtags TEXT[],
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, approved, rejected, published
    chief_notes TEXT,
    reviewed_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    late_dev_post_id TEXT,  -- response from Late.dev API
    engagement_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_linkedin_drafts_status ON linkedin_drafts(status);