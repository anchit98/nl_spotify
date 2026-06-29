-- Add top_themes to question_answers (run once on existing insights schema)

ALTER TABLE insights.question_answers
    ADD COLUMN IF NOT EXISTS top_themes JSONB NOT NULL DEFAULT '[]'::jsonb;
