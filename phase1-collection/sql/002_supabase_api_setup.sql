-- Run after 001_raw_schema.sql so the Supabase REST API can read/write the raw zone.
-- Also add "raw" under Dashboard -> Project Settings -> API -> Exposed schemas.

GRANT USAGE ON SCHEMA raw TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw TO anon, authenticated, service_role;
GRANT SELECT ON raw.last_successful_run TO anon, authenticated, service_role;

-- Phase 1 collection runs from GitHub Actions using the anon key in secrets.
-- Disable RLS on raw tables for now; tighten in a later phase if needed.
ALTER TABLE raw.collection_runs DISABLE ROW LEVEL SECURITY;
ALTER TABLE raw.feedback_items DISABLE ROW LEVEL SECURITY;
