# Phase 5: Continuous Monitoring, Feedback Loop and Iteration

Keeps the pipeline healthy after Phase 4 go-live. Implements [architecture.md](../docs/architecture.md) Phase 5 in a standalone ops package.

## What this phase delivers

| Output | Implementation |
|--------|----------------|
| **Trend tracking** | `ops.theme_trends` — theme mention counts per synthesis run; spike detection across last 2 runs |
| **Run history / audit log** | `ops.health_snapshots` — weekly corpus, per-source collection, synthesis status |
| **Failure notifications** | `ops.alerts` + optional `ALERT_WEBHOOK_URL` (Slack/Discord-compatible) |
| **Model / prompt pinning** | `config/model_pin.yaml` + `ops.model_registry` |
| **Product feedback loop** | `ops.review_actions` + [docs/feedback-loop.md](docs/feedback-loop.md) |

## Setup

1. **Supabase SQL** — run in order:
   - `sql/001_ops_schema.sql`
   - `sql/002_ops_api_setup.sql`
2. **Expose `ops` schema** — Supabase Dashboard → API → Exposed schemas → add `ops`.
3. **Environment** — copy `.env.example` values into repo-root `.env` (or GitHub Actions secrets):

```bash
SUPABASE_PROJECT_URL=...
SUPABASE_PROJECT_ANON_KEY=...
ALERT_WEBHOOK_URL=https://hooks.slack.com/...   # optional
GROQ_MODEL=llama-3.3-70b-versatile
PROMPT_VERSION=2026-06-v1
```

4. **Install:**

```bash
cd phase5-operations
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run locally

```bash
set PYTHONPATH=src
python -m phase5_ops.runner monitor --trigger manual
```

Reports are written to `reports/latest_health_report.md` and `.json`.

### Pipeline failure alert (manual)

```bash
python -m phase5_ops.runner pipeline-failure --workflow "Data Pipeline" --job "synthesize" --error "Groq quota exceeded"
```

## GitHub Actions

- **[`.github/workflows/phase5-monitor.yml`](../.github/workflows/phase5-monitor.yml)** — runs after the weekly pipeline (or on schedule / manual dispatch).
- **`pipeline.yml`** — posts a failure alert when any Phase 1–3 job fails.

Add secret: `ALERT_WEBHOOK_URL` (optional).

## Configuration

| File | Purpose |
|------|---------|
| `config/alert_thresholds.yaml` | Drift and spike thresholds (edge case 5.1, 5.2) |
| `config/model_pin.yaml` | Pinned Groq model + prompt version (edge case 5.3) |

Bump `prompt_version` in both `model_pin.yaml` and `PROMPT_VERSION` env when `phase3_insights/prompts.py` changes materially.

## Weekly product review

Use [docs/weekly-review-template.md](docs/weekly-review-template.md) with the latest health report and dashboard export.

## Database tables (`ops` schema)

- `health_snapshots` — point-in-time pipeline metrics
- `theme_trends` — theme mentions per synthesis run
- `alerts` — fired alerts (deduped 24h by category+title)
- `model_registry` — model/prompt version history
- `review_actions` — product-team actions from feedback loop meetings

## Next step

After ops is live, continue with [deployment.md](../docs/deployment.md) (Phase 6) if not already deployed, then tune thresholds in `config/alert_thresholds.yaml` based on real alert volume.
