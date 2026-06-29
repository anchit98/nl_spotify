-- Run after 001_clean_schema.sql so the Supabase REST API can read/write the clean zone.
-- IMPORTANT: You must also add "clean" under Dashboard -> Project Settings -> API -> Exposed schemas.

GRANT USAGE ON SCHEMA clean TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA clean TO anon, authenticated, service_role;

-- Disable RLS on clean tables for now so the Python script can write to them using the anon key.
ALTER TABLE clean.feedback_items DISABLE ROW LEVEL SECURITY;
ALTER TABLE clean.processed_raw_items DISABLE ROW LEVEL SECURITY;
ALTER TABLE clean.cleaning_runs DISABLE ROW LEVEL SECURITY;
