# Phase 1: Setup and Data Collection

Collects **publicly viewable** feedback from five sources and stores untouched JSON in Supabase (`raw` schema). No Reddit, Twitter, or paid API keys are required.

## Sources (all public)

| Source | How we access it | Keys needed |
|---|---|---|
| App Store | Apple customer-reviews RSS | None |
| Google Play | Public Play Store review data | None |
| Reddit | PullPush public archive API | None |
| Community forum | Public Spotify Community search pages | None |
| Social media | Mastodon public tag timelines | None |

## Collection modes

All modes **append** to existing data (upsert on `source` + `source_item_id`; duplicates are skipped).

| Mode | When to use | Time window | Volume limits |
|---|---|---|---|
| `initial` | One-time bootstrap before go-live | `INITIAL_LOOKBACK_DAYS` (default 90) | **None** — paginate until the source is exhausted |
| `weekly` | Scheduled Monday cron (default) | Since last successful run per source | Paginate within window |
| `adhoc` | Dashboard button or manual workflow | `ADHOC_LOOKBACK_DAYS` (default **7**) | Paginate within window |
| `probe` | Connectivity / volume estimate | Same as initial window | One small page per source |

```bash
python -m phase1_collection.runner --initial    # one-time full extract
python -m phase1_collection.runner              # weekly incremental (default)
python -m phase1_collection.runner --adhoc      # last 7 days
python -m phase1_collection.runner --probe      # smoke test
```

After go-live, only **weekly** and **adhoc** runs are expected. Re-run `--initial` only if you deliberately need to backfill again.

## Setup

1. **Supabase SQL** — run in the SQL Editor, in order:
   - `sql/001_raw_schema.sql`
   - `sql/002_supabase_api_setup.sql`
2. **Expose the `raw` schema** — Supabase Dashboard → Project Settings → API → **Exposed schemas** → add `raw`.
3. **Environment** — copy `.env.example` to the repo-root `.env` (or `phase1-collection/.env`) and set:
   - `SUPABASE_PROJECT_URL`
   - `SUPABASE_PROJECT_ANON_KEY`
   - `SUPABASE_JWT_SECRET` (optional for now; reserved for custom JWT signing later)
   - `INITIAL_LOOKBACK_DAYS` (default 90)
   - `ADHOC_LOOKBACK_DAYS` (default 7)
4. **Legal sign-off** — `config/source_signoff.yaml` is pre-filled for public methods; re-confirm terms before production.

## Local run

```bash
cd phase1-collection
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
set PYTHONPATH=src              # Windows
python -m phase1_collection.runner --probe
python -m phase1_collection.runner --initial
```

On macOS/Linux use `export PYTHONPATH=src` and `source .venv/bin/activate`.

## GitHub Actions

Workflow: `.github/workflows/phase1-collection.yml`

- **Schedule:** every Monday 02:00 UTC — `weekly` mode (incremental).
- **Manual dispatch:** choose `weekly`, `adhoc`, `initial`, or `probe`.

Add these repository secrets:

- `SUPABASE_PROJECT_URL`
- `SUPABASE_PROJECT_ANON_KEY`

Optional: `SUPABASE_JWT_SECRET` if you add custom JWT auth later.

## Edge cases handled

- **1.1** — `--probe` estimates volume before the first `--initial` run.
- **1.3** — each source is collected independently; one failure does not block others.
- **1.4** — weekly mode starts at last successful `window_end`; missed weeks are caught up automatically. Ad-hoc is fixed at 7 days.
- **1.5** — upsert on `(source, source_item_id)` ignores duplicates.
- **1.7** — preflight checks Supabase URL + anon key before any network calls.
