-- Run after 001_insights_schema.sql
-- Also add "insights" under Dashboard -> Project Settings -> API -> Exposed schemas

GRANT USAGE ON SCHEMA insights TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA insights TO anon, authenticated, service_role;

ALTER TABLE insights.synthesis_runs DISABLE ROW LEVEL SECURITY;
ALTER TABLE insights.question_answers DISABLE ROW LEVEL SECURITY;
ALTER TABLE insights.executive_summary DISABLE ROW LEVEL SECURITY;
