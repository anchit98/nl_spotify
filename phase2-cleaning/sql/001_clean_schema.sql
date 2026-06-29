-- Create the clean schema
CREATE SCHEMA IF NOT EXISTS clean;

-- Create the cleaned feedback items table
CREATE TABLE IF NOT EXISTS clean.feedback_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_id UUID REFERENCES raw.feedback_items(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    source_item_id TEXT NOT NULL,
    posted_at TIMESTAMPTZ,
    cleaned_text TEXT NOT NULL,
    rating INTEGER,
    language TEXT,
    country TEXT,
    user_hints JSONB,
    topics_matched JSONB,
    cleaned_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(source, source_item_id)
);

CREATE TABLE IF NOT EXISTS clean.processed_raw_items (
    raw_id UUID PRIMARY KEY,
    processed_at TIMESTAMPTZ DEFAULT now(),
    kept BOOLEAN NOT NULL,
    drop_reason TEXT
);

-- Create a table to track cleaning runs
CREATE TABLE IF NOT EXISTS clean.cleaning_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    items_processed INTEGER DEFAULT 0,
    items_kept INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB
);

-- RPC to get unprocessed raw items
CREATE OR REPLACE FUNCTION clean.get_unprocessed_raw_items(batch_size INT)
RETURNS SETOF raw.feedback_items
LANGUAGE sql
SECURITY DEFINER
AS $$
    SELECT r.*
    FROM raw.feedback_items r
    LEFT JOIN clean.processed_raw_items p ON r.id = p.raw_id
    WHERE p.raw_id IS NULL
    ORDER BY r.posted_at ASC NULLS LAST
    LIMIT batch_size;
$$;
