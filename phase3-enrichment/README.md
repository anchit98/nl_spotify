# Phase 3: Insight Generation (SQL aggregation + Groq synthesis)

Aggregates all cleaned feedback from the `clean` schema in Python (no Groq cost), then uses **~7 Groq calls** to answer the six research questions and draft an executive summary.

## What it produces

Writes to the `insights` schema in Supabase:

| Table | Description |
|---|---|
| `synthesis_runs` | Run metadata, token usage, status |
| `question_answers` | Narrative answer per research question with **5 top themes**, stats, and quotes |
| `executive_summary` | Top pain points, opportunities, and headline summary |

Phase 2 already tags each row with `topics_matched`. Phase 3 maps those topics to the six questions, counts mentions by source/rating, selects up to 30 representative quotes per question, and sends that bundle to Groq.

## Edge cases handled

- **3.1** — Groq rate limits with backoff; stops cleanly when daily quota is exhausted
- **3.2** — Strict JSON schema validation on synthesis output
- **3.3** — Volume vs importance scoring in aggregation (frequency + rating + source spread)
- **3.4** — Thin segments and missing segment hints reported honestly
- **3.5** — Every narrative anchored to provided stats and quotes (no full-corpus hallucination)

## Setup

1. Run SQL in Supabase (in order):
   - `sql/001_insights_schema.sql`
   - `sql/002_insights_api_setup.sql`
   - `sql/003_add_top_themes_column.sql` (if `001` was run before themes were added)
2. Expose the **`insights`** schema in Supabase Dashboard → API → Exposed schemas.
3. Set `GROQ_API_KEY` in repo-root `.env`.

## Groq rate limits (`llama-3.3-70b-versatile`)

| Limit | Value |
|---|---|
| Requests / minute | 30 |
| Requests / day | 1,000 |
| Tokens / minute | 12,000 |
| Tokens / day | 100,000 |

A full synthesis run uses ~7 requests and ~30–50k tokens — well within the free-tier daily cap. Probe mode uses 2 questions on up to 200 clean items.

## Local run

```bash
cd phase3-enrichment
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set PYTHONPATH=src
python -m phase3_insights.synthesizer --probe    # smoke test (2 questions)
python -m phase3_insights.synthesizer            # full run (6 questions + executive summary)
```

## Environment

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | — | Required |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Model slug |
| `SKIP_EXECUTIVE_SUMMARY` | `false` | Skip the 7th Groq call |
| `GROQ_RATE_LIMIT_SAFETY_MARGIN` | `0.05` | Buffer below daily quota |
