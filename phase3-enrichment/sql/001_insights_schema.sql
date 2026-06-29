-- Phase 3 (pivoted): Insight generation — SQL aggregates + Groq synthesis
-- Replaces the previous per-item enriched schema approach.

CREATE SCHEMA IF NOT EXISTS insights;

CREATE TABLE IF NOT EXISTS insights.synthesis_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    clean_items_analyzed INTEGER DEFAULT 0,
    questions_answered INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS insights.question_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES insights.synthesis_runs(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL,
    question_text TEXT NOT NULL,
    answer_narrative TEXT NOT NULL,
    key_findings JSONB NOT NULL DEFAULT '[]'::jsonb,
    top_themes JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_quotes JSONB NOT NULL DEFAULT '[]'::jsonb,
    stats JSONB NOT NULL DEFAULT '{}'::jsonb,
    model_version TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(run_id, question_id)
);

CREATE TABLE IF NOT EXISTS insights.executive_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES insights.synthesis_runs(id) ON DELETE CASCADE,
    summary_text TEXT NOT NULL,
    top_pain_points JSONB NOT NULL DEFAULT '[]'::jsonb,
    top_opportunities JSONB NOT NULL DEFAULT '[]'::jsonb,
    model_version TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(run_id)
);
