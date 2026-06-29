-- Run after 001_ops_schema.sql. Add "ops" under Supabase API -> Exposed schemas.

GRANT USAGE ON SCHEMA ops TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ops TO anon, authenticated, service_role;

ALTER TABLE ops.health_snapshots DISABLE ROW LEVEL SECURITY;
ALTER TABLE ops.theme_trends DISABLE ROW LEVEL SECURITY;
ALTER TABLE ops.alerts DISABLE ROW LEVEL SECURITY;
ALTER TABLE ops.model_registry DISABLE ROW LEVEL SECURITY;
ALTER TABLE ops.review_actions DISABLE ROW LEVEL SECURITY;
