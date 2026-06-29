-- Phase 5: Operations — monitoring, theme trends, alerts, model registry, feedback loop

CREATE SCHEMA IF NOT EXISTS ops;

-- Weekly (or per-pipeline) health snapshot for drift detection
CREATE TABLE IF NOT EXISTS ops.health_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    trigger TEXT NOT NULL DEFAULT 'manual',
    corpus_clean_total INTEGER NOT NULL DEFAULT 0,
    corpus_rated_total INTEGER NOT NULL DEFAULT 0,
    collection_by_source JSONB NOT NULL DEFAULT '{}'::jsonb,
    collection_failures INTEGER NOT NULL DEFAULT 0,
    latest_synthesis_run_id UUID,
    synthesis_status TEXT,
    synthesis_questions_answered INTEGER,
    synthesis_tokens_used INTEGER,
    synthesis_model TEXT,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_health_snapshots_captured
    ON ops.health_snapshots (captured_at DESC);

-- Theme mention counts per synthesis run (for rising-theme detection)
CREATE TABLE IF NOT EXISTS ops.theme_trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    synthesis_run_id UUID NOT NULL,
    question_id TEXT NOT NULL,
    theme TEXT NOT NULL,
    mention_count INTEGER NOT NULL DEFAULT 0,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (synthesis_run_id, question_id, theme)
);

CREATE INDEX IF NOT EXISTS idx_theme_trends_question_theme
    ON ops.theme_trends (question_id, theme, captured_at DESC);

-- Fired alerts (audit trail + dedupe reference)
CREATE TABLE IF NOT EXISTS ops.alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fired_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    context JSONB NOT NULL DEFAULT '{}'::jsonb,
    notified BOOLEAN NOT NULL DEFAULT false,
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_alerts_fired
    ON ops.alerts (fired_at DESC);

-- Pinned model + prompt version history (edge case 5.3)
CREATE TABLE IF NOT EXISTS ops.model_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    groq_model TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    notes TEXT,
    changed_by TEXT DEFAULT 'system',
    UNIQUE (groq_model, prompt_version)
);

-- Product-team actions from the weekly feedback loop
CREATE TABLE IF NOT EXISTS ops.review_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_date DATE NOT NULL DEFAULT CURRENT_DATE,
    synthesis_run_id UUID,
    insight_summary TEXT NOT NULL,
    action_owner TEXT,
    action_due DATE,
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'in_progress', 'done', 'wont_fix')),
    outcome_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_review_actions_status
    ON ops.review_actions (status, review_date DESC);
