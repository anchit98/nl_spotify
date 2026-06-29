-- Phase 1: raw zone in Supabase Postgres
-- Run once in Supabase SQL Editor (or via migration tooling in Phase 7).

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.collection_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status IN ('running', 'success', 'failed')),
    items_collected INTEGER NOT NULL DEFAULT 0,
    window_start TIMESTAMPTZ,
    window_end TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    error_message TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_collection_runs_source_started
    ON raw.collection_runs (source, started_at DESC);

CREATE TABLE IF NOT EXISTS raw.feedback_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,
    source_item_id TEXT NOT NULL,
    run_id UUID NOT NULL REFERENCES raw.collection_runs (id) ON DELETE CASCADE,
    posted_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_payload JSONB NOT NULL,
    CONSTRAINT uq_feedback_source_item UNIQUE (source, source_item_id)
);

CREATE INDEX IF NOT EXISTS idx_feedback_items_source_posted
    ON raw.feedback_items (source, posted_at DESC);

CREATE INDEX IF NOT EXISTS idx_feedback_items_run_id
    ON raw.feedback_items (run_id);

-- Last successful collection watermark per source (edge case 1.4: window-based catch-up)
CREATE OR REPLACE VIEW raw.last_successful_run AS
SELECT DISTINCT ON (source)
    source,
    completed_at AS last_success_at,
    window_end AS last_window_end
FROM raw.collection_runs
WHERE status = 'success'
ORDER BY source, completed_at DESC;
