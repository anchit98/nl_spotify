# Backend — FastAPI (Phase 4)

Serves insights from Supabase, live review trends, synthesis triggers, and the PM Buddy chat copilot.

## Run locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set PYTHONPATH=src
uvicorn backend_api.main:app --reload --port 8000
```

Requires repo-root `.env` with:

- Supabase credentials (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` or equivalent)
- `GROQ_API_KEY` and `GROQ_MODEL` (synthesis and PM Buddy chat)
- Phase 3 installed in `phase3-enrichment/`

**Production deploy:** see [docs/deployment.md](../docs/deployment.md) (Render + Vercel + GitHub Actions).

**Note:** If you restart the backend after adding routes, ensure no orphaned uvicorn worker is still listening on port 8000 (a stale process can serve old code and return 404 for new endpoints such as PM Buddy).

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/insights/latest` | Latest successful run bundle; KPIs refreshed from live `dataset_stats` and quotes re-selected on read |
| GET | `/api/insights/runs` | Run history |
| GET | `/api/insights/runs/{id}` | Specific run bundle |
| GET | `/api/insights/trends?granularity=week\|month\|year` | Live review trends from `clean.feedback_items` (volume, avg rating, net sentiment by period) |
| GET | `/api/synthesis/status` | Whether synthesis is in progress |
| POST | `/api/synthesize` | Start full pipeline: incremental collection → clean new items → synthesize (409 if already running) |
| POST | `/api/cache/invalidate` | Clear in-memory API caches (call after synthesis completes) |
| POST | `/api/pm-buddy/chat` | Groq chat for repetitive-listening / discovery strategy (503 if `GROQ_API_KEY` missing) |

## Trends sentiment methodology

Trend **sentiment score** is derived from star ratings, not NLP text analysis:

- 4–5★ → positive, 3★ → neutral, 1–2★ → negative
- **Net sentiment %** = `(positive − negative) / rated_count × 100` (range −100 to +100)
- Unrated reviews count toward volume but not toward sentiment or average rating

## PM Buddy

`POST /api/pm-buddy/chat` accepts `{ message, history? }` and builds context from dataset stats, repetitive-listening signals, segment breakdown, latest synthesis, and sample quotes before calling Groq. History is capped to the last 10 turns.

## Synthesize now pipeline

`POST /api/synthesize` runs in a background thread:

1. **Phase 1** — `phase1_collection.runner --mode weekly` (incremental since each source's last successful `window_end`)
2. **Phase 2** — `phase2_cleaning.cleaner` (only unprocessed raw rows)
3. **Phase 3** — `phase3_insights.synthesizer` (full corpus)

Each phase uses its own `.venv` under `phase1-collection/`, `phase2-cleaning/`, and `phase3-enrichment/` when present. Response caches are cleared before and after synthesis.
