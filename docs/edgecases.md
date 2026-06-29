# Edge Cases and Failure Modes

## How to read this document

This document is the companion to [architecture.md](architecture.md). The architecture document explains how the system is **meant** to work. This document explains everything that can **go wrong**, and what we do about it.

It is written in the same plain English so that anyone - technical or not - can follow along.

Each edge case is described with the same five parts:

- **What happens** - the problem, in plain English.
- **Why it matters** - the damage if we ignore it.
- **Prevent** - how we stop it from happening in the first place.
- **Detect** - how we notice it quickly when it does happen.
- **Recover** - how we get back to normal.

The cases are grouped to match the architecture: a short **setup guardrails** section (mirroring "Before we build"), then the **six build phases**, then a set of **cross-cutting concerns** that touch every phase.

A quick reminder of the chosen tools (all explained in the architecture glossary): Python + FastAPI backend on Render, Next.js frontend on Vercel, Groq as the LLM provider, Supabase Postgres as the database, and GitHub Actions for the weekly collection and synthesis jobs.

---

## Setup guardrails (before we build)

### S.1 A source's terms of service forbid the way we collect

- **What happens:** We design the pipeline around a source, then discover its terms of service do not allow automated collection or storage.
- **Why it matters:** Legal and reputational risk, and possibly throwing away work built on that source.
- **Prevent:** Confirm each source's terms before building its connector; record the decision per source.
- **Detect:** Periodic re-review of terms, since they change without notice.
- **Recover:** Drop or replace the source, and clearly mark any insights that relied on it so they are not trusted blindly.

---

## Phase 1 - Setup and Data Collection (GitHub Actions weekly job)

### 1.1 The initial extract returns far more (or far less) data than expected

- **What happens:** A source that we thought had a few thousand posts in three months actually has hundreds of thousands, or almost none.
- **Why it matters:** Too much data blows past rate limits and Groq cost budgets; too little makes a source statistically useless.
- **Prevent:** Run `--probe` before the one-time `--initial` extract to estimate real volume. Initial mode has no artificial pagination caps — only source API limits apply.
- **Detect:** Compare actual initial-run counts against the probe estimate.
- **Recover:** Narrow `INITIAL_LOOKBACK_DAYS`, sample the data, or down-weight a thin source in the analysis.

### 1.2 A source offers no official API, only a public webpage

- **What happens:** We must read the page like a human (scraping) instead of asking through a clean front door.
- **Why it matters:** Scrapers are fragile - they break whenever the page layout changes.
- **Prevent:** Prefer official APIs; isolate any scraping logic so it can be fixed without touching the rest.
- **Detect:** A connector health check that flags when expected fields suddenly come back empty.
- **Recover:** Patch the scraper against the new layout; backfill the missed window on the next run.

### 1.3 The weekly GitHub Actions run fails partway through

- **What happens:** The job collects two of five sources, then crashes (network blip, timeout, runner killed).
- **Why it matters:** A half-finished run can leave the raw data in a confusing, partial state.
- **Prevent:** Make each source's collection a separate, independent step; write data per source and per run so a partial run is still usable.
- **Detect:** GitHub Actions marks the run red; a failure notification is sent.
- **Recover:** Re-run the workflow; because each source writes independently, only the missing sources need to be re-collected.

### 1.4 A weekly run is missed entirely (e.g. GitHub Actions outage or disabled schedule)

- **What happens:** A scheduled weekly cron simply does not fire, so a week of data is never collected.
- **Why it matters:** A permanent hole in the timeline that later trend charts cannot explain.
- **Prevent:** Weekly mode collects "since the last successful run" (not a fixed 7-day window), so a skipped week is automatically caught up next time. Ad-hoc mode is intentionally fixed at 7 days for quick refreshes only.
- **Detect:** A freshness check that alerts if no successful weekly run has completed in more than 8 days.
- **Recover:** Manually trigger the workflow in `weekly` mode; the window-based logic backfills the gap.

### 1.5 Duplicate collection on a re-run

- **What happens:** A re-run pulls the same posts again, creating duplicates in the raw zone.
- **Why it matters:** Inflated counts make a complaint look more common than it is.
- **Prevent:** Store each item with its source-provided unique ID and use an "insert only if new" write into Supabase Postgres.
- **Detect:** A data-quality check comparing row counts before and after de-duplication.
- **Recover:** De-duplication happens in Phase 2 anyway, so duplicates in raw are tolerable and cleaned downstream.

### 1.6 A source changes its data format silently

- **What happens:** A field we depend on is renamed, removed, or starts arriving in a new shape.
- **Why it matters:** The connector either crashes or, worse, quietly stores blanks.
- **Prevent:** Validate the shape of incoming data at collection time and fail loudly on surprises.
- **Detect:** The shape check flags missing or unexpected fields.
- **Recover:** Update the connector; re-collect the affected window.

### 1.7 Secrets are missing or expired in GitHub Actions

- **What happens:** The Groq key, database URL, or a source API key stored in GitHub secrets is missing or has expired.
- **Why it matters:** The whole weekly job fails before it does anything useful.
- **Prevent:** A pre-flight step at the start of the workflow that checks every required secret is present.
- **Detect:** The pre-flight step fails fast with a clear message naming the missing secret.
- **Recover:** Add or rotate the secret in GitHub settings; re-run.

---

## Phase 2 - Storage, Standardization and Cleaning (Supabase Postgres)

### 2.1 Feedback in an unexpected language or character set

- **What happens:** Posts arrive in scripts or emoji-heavy text that our language detection mishandles.
- **Why it matters:** Mislabeled language sends text to the wrong NLP path, or drops it entirely.
- **Prevent:** Store the original text untouched; treat language detection as a best-effort tag, not a gate.
- **Detect:** A report of how much text was tagged "unknown language".
- **Recover:** Route "unknown" text through translation anyway, or hold it aside for manual review.

### 2.2 Over-aggressive cleaning removes real user voice

- **What happens:** Filters meant to remove spam also strip out sarcasm, slang, or short-but-meaningful posts.
- **Why it matters:** We lose exactly the candid feedback we set out to capture.
- **Prevent:** Keep the raw zone untouched; cleaning only ever writes to the clean schema, never deletes raw.
- **Detect:** Spot-check a sample of dropped records to confirm they really were junk.
- **Recover:** Loosen the filter and re-run cleaning from the raw zone - no re-collection needed.

### 2.3 The clean record loses its link back to the raw record

- **What happens:** A cleaned row cannot be traced to the original post.
- **Why it matters:** We cannot audit a surprising insight or show the original quote.
- **Prevent:** Every clean row carries the raw row's unique ID.
- **Detect:** A check that every clean row has a valid raw reference.
- **Recover:** Re-run cleaning from raw, which restores the link.

### 2.4 The database fills up or a write fails mid-batch

- **What happens:** Supabase Postgres runs out of space, or a large write is interrupted.
- **Why it matters:** Partial writes can corrupt a batch and stall the pipeline.
- **Prevent:** Write in transactions (all-or-nothing batches); monitor database size against the plan limit.
- **Detect:** Storage alerts and failed-transaction logs.
- **Recover:** Re-run the failed batch (transactions guarantee it was not half-applied); upgrade storage if the limit is the cause.

---

## Phase 3 - Insight Generation (SQL aggregation + Groq synthesis)

### 3.1 Groq is rate-limited or temporarily unavailable

- **What happens:** We send synthesis requests faster than Groq allows, or Groq has an outage mid-run.
- **Why it matters:** Some research questions may be unanswered in this run.
- **Prevent:** Only ~7 Groq calls per full run; backoff between calls; save each answer as it completes.
- **Detect:** Count of failed or skipped questions in the run log.
- **Recover:** Re-run synthesis on the next window; partial runs are resumable because each question is written independently.

### 3.2 Groq returns malformed or non-JSON output

- **What happens:** The model returns text that does not match the structured format we asked for.
- **Why it matters:** A question answer cannot be saved or shown on the dashboard.
- **Prevent:** Ask for a strict structured format and validate every response before saving.
- **Detect:** A parse-failure counter per run.
- **Recover:** Re-prompt the failed question with a stricter instruction; mark the run partial if it still fails.

### 3.3 Volume is mistaken for importance

- **What happens:** A theme that is mentioned often is treated as the top priority, even though it is mild.
- **Why it matters:** The team fixes loud-but-minor issues while big-but-quiet ones are ignored.
- **Prevent:** Score pain points on frequency, low star ratings, and spread across sources together during aggregation, not just count.
- **Detect:** Sanity review comparing the ranked list against known major complaints.
- **Recover:** Re-weight the scoring and regenerate the synthesis.

### 3.4 A segment has too few records to trust

- **What happens:** We slice by a narrow segment (for example, one country and one genre) and only a handful of posts remain.
- **Why it matters:** A handful of posts can swing a percentage wildly and produce a false "trend".
- **Prevent:** Set a minimum sample size before a segment-level claim is shown.
- **Detect:** Flag any segment chart built on fewer than the minimum.
- **Recover:** Merge thin segments or label them clearly as "low confidence".

### 3.5 Segment hints are missing or guessed

- **What happens:** Many sources do not tell us if a user is free vs premium or new vs long-time, so segmentation is incomplete.
- **Why it matters:** Segment comparisons may be based on a small, biased subset that has hints.
- **Prevent:** Treat "unknown" as its own honest segment rather than guessing.
- **Detect:** Report what share of records have each segment attribute.
- **Recover:** Caveat segment findings with the coverage percentage.

### 3.6 Groq summaries drift from the underlying data

- **What happens:** The synthesis pass overstates or softens what the aggregated stats and quotes show.
- **Why it matters:** Decision-makers act on a summary that the numbers do not support.
- **Prevent:** Send only pre-computed stats and selected quotes to Groq; require citations in the output schema.
- **Detect:** Cross-check a sample of summary claims against the stats behind them.
- **Recover:** Regenerate with a stricter, evidence-bound prompt.

### 3.7 Daily token budget is exhausted before all questions finish

- **What happens:** Earlier Groq calls in the day used most of the free-tier quota, so synthesis cannot complete.
- **Why it matters:** The dashboard shows stale or partial answers.
- **Prevent:** Check remaining quota before starting; a full run needs ~30–50k tokens (~7 calls).
- **Detect:** Preflight reports insufficient quota; run log shows partial `questions_answered`.
- **Recover:** Finish on the next day when the daily cap resets; probe mode (`--probe`) validates the pipeline cheaply.

---

## Phase 4 - Visualization and Storytelling (Next.js on Vercel) and the synthesis triggers

### 4.1 The "Synthesize now" button is pressed many times in a row

- **What happens:** An impatient user clicks **Synthesize now** on the home header repeatedly, kicking off overlapping synthesis runs.
- **Why it matters:** Wasted Groq cost, possible race conditions, and confusing half-updated results.
- **Prevent:** Disable the button while a run is in progress; allow only one active synthesis at a time on the backend.
- **Detect:** The backend rejects a new request while one is running and tells the user it is already in progress.
- **Recover:** Show the status of the in-flight run; no manual cleanup needed because overlaps are blocked.

### 4.2 The weekly run and an ad-hoc run collide

- **What happens:** A user presses "Synthesize now" (which triggers a 7-day ad-hoc collection plus synthesis) just as the weekly GitHub Actions job starts.
- **Why it matters:** Two runs writing insights at once can interleave and corrupt the latest results.
- **Prevent:** A single shared lock that both the button and the weekly job must acquire before writing.
- **Detect:** The second run sees the lock and waits or declines.
- **Recover:** The blocked run retries after the first finishes; the lock guarantees a clean, single writer.

### 4.3 The dashboard loads while a synthesis is mid-write

- **What happens:** A user opens the dashboard exactly when insights are being rewritten.
- **Why it matters:** They might see a mix of old and new numbers.
- **Prevent:** Write new insights as a new version and switch the dashboard to it only once complete (no partial reads).
- **Detect:** A version/timestamp shown on the dashboard so stale or mid-write states are visible.
- **Recover:** Refresh once the new version is published; the previous version stays readable until then.

### 4.4 The backend (Render) is asleep or slow on first request

- **What happens:** On lower Render tiers the backend spins down when idle and takes seconds to wake.
- **Why it matters:** The first dashboard load or button press looks broken.
- **Prevent:** Show a clear loading state; optionally keep the service warm with a light periodic ping.
- **Detect:** Slow first-response timing in logs.
- **Recover:** The request succeeds once awake; the loading state sets the right expectation.

### 4.5 The frontend cannot reach the backend (CORS, wrong URL, downtime)

- **What happens:** The Vercel frontend calls the Render backend but the request is blocked or misrouted.
- **Why it matters:** A blank or broken dashboard with no explanation.
- **Prevent:** Configure allowed origins explicitly; store the backend URL as a per-environment variable so staging and production never cross.
- **Detect:** Frontend error logging and a visible error message instead of a blank screen.
- **Recover:** Fix the origin or URL setting and redeploy; the frontend retries.

### 4.6 No data yet, or empty results for a question

- **What happens:** Before the first run, or for a question with no matching feedback, a page has nothing to show.
- **Why it matters:** An empty chart looks like a bug and erodes trust.
- **Prevent:** Design explicit "no data yet" and "not enough data" states for every page.
- **Detect:** Covered by design review and tests with empty inputs.
- **Recover:** Not applicable - this is a design state, not a failure.

### 4.7 PM Buddy is used but Groq is not configured

- **What happens:** A user opens PM Buddy and sends a message while `GROQ_API_KEY` is missing on the backend.
- **Why it matters:** Chat appears broken with no clear explanation.
- **Prevent:** Configure `GROQ_API_KEY` in every backend environment; return 503 with a clear message when absent.
- **Detect:** PM Buddy requests fail with 503; health check still passes.
- **Recover:** Add the key and restart the backend (ensure no stale worker on port 8000).

### 4.8 An orphaned backend worker serves old routes

- **What happens:** After code changes, an old uvicorn multiprocessing child keeps listening on port 8000 while the parent process is gone.
- **Why it matters:** New endpoints (for example `/api/pm-buddy/chat`) return 404 even though the codebase is correct.
- **Prevent:** Stop all Python/uvicorn processes on port 8000 before restarting; use `--reload` only in development.
- **Detect:** Route exists in code but returns 404; netstat shows a listener whose parent PID no longer exists.
- **Recover:** Kill the orphaned process and start a fresh backend.

### 4.9 PDF export fails on modern CSS colour functions

- **What happens:** **Export Report** uses `html2canvas`, which cannot parse Tailwind v4 `oklab()` colours in stylesheets.
- **Why it matters:** PDF generation throws a parse error and the export button appears broken.
- **Prevent:** During canvas clone, strip external stylesheets and inline computed RGB styles on captured nodes.
- **Detect:** Console error mentioning `oklab` during export.
- **Recover:** Already handled in the export pipeline; if it regresses, re-apply the inline-RGB clone step.

### 4.10 Trends sentiment is mistaken for NLP text sentiment

- **What happens:** Users interpret the trends sentiment line as Groq-analysed tone from review text.
- **Why it matters:** Rating distributions can look positive while written complaints dominate, or vice versa.
- **Prevent:** Label trends clearly as rating-based net sentiment; document methodology in architecture and backend README.
- **Detect:** User or stakeholder questions why sentiment diverges from quoted complaints.
- **Recover:** Explain the proxy; future enhancement could add true text sentiment as a separate series.

---

## Phase 5 - Continuous Monitoring, Feedback Loop and Iteration

### 5.1 The pipeline silently rots after launch

- **What happens:** Runs keep "succeeding" but the data quietly degrades (a source drying up, topic coverage going stale).
- **Why it matters:** The team trusts a dashboard that is slowly becoming wrong.
- **Prevent:** Track per-run health metrics (volume per source, synthesis success rate) over time, not just pass/fail.
- **Detect:** Alerts when any metric drifts far from its recent norm.
- **Recover:** Investigate the drifting metric; fix the source or the prompt behind it.

### 5.2 A genuine spike is mistaken for noise (or vice versa)

- **What happens:** A real surge in a complaint is dismissed, or a one-off blip triggers a false alarm.
- **Why it matters:** Either a missed emerging issue or alert fatigue.
- **Prevent:** Base alerts on sustained change across multiple runs, not a single point.
- **Detect:** Review flagged spikes against the raw quotes behind them.
- **Recover:** Tune the alert threshold; confirm with human judgement before escalating.

### 5.3 Model behaviour drifts as Groq models are updated

- **What happens:** A newer model version summarises differently than before.
- **Why it matters:** Trends break because the measurement itself changed, not the data.
- **Prevent:** Pin the model version; record which version produced each run.
- **Detect:** A noticeable step-change in answers right after a version change.
- **Recover:** Re-run recent windows on a consistent version when comparing trends.

---

## Phase 6 - Deployment, CI/CD and Fail-proofing

### 6.1 A bad commit reaches production

- **What happens:** Broken code is merged and deployed to the live backend or frontend.
- **Why it matters:** A user-facing outage.
- **Prevent:** Branch protection on `main`; required CI checks (lint, type-check, tests, a tiny Groq smoke test) before merge; deploy to staging first.
- **Detect:** Render and Vercel health checks fail on the new deploy.
- **Recover:** Automatic rollback to the last healthy deploy; fix forward in a new commit (never amend a shipped one).

### 6.2 A secret leaks into the repository

- **What happens:** The Groq key, database URL, or a source key is accidentally committed to GitHub.
- **Why it matters:** Anyone with repo access (or the public) could use or abuse the key.
- **Prevent:** Keep all secrets in GitHub Actions secrets, Render's secret store, and Vercel environment variables - never in code; add secret-scanning and a pre-commit check. The local `.env` file must be git-ignored.
- **Detect:** Secret-scanning flags the commit.
- **Recover:** Rotate the leaked key immediately; purge it from history; follow the break-glass runbook.

### 6.3 Staging and production get crossed

- **What happens:** The production frontend points at the staging backend, or staging writes into the production database.
- **Why it matters:** Test data pollutes real insights, or real users see test data.
- **Prevent:** Separate environment variables and separate databases per environment; never share a connection string.
- **Detect:** An environment banner on non-production sites; a startup check that refuses mismatched pairings.
- **Recover:** Correct the environment variable and redeploy.

### 6.4 A database migration fails or locks the table

- **What happens:** A schema change errors midway or holds a long lock during deploy.
- **Why it matters:** The backend can be left talking to a half-migrated database.
- **Prevent:** Run migrations as a separate step before the backend deploys, with a dry-run first; prefer additive, backward-compatible changes.
- **Detect:** The migration step fails and halts the deploy before the new backend goes live.
- **Recover:** Roll back the migration or apply the prepared down-migration; keep the previous backend running until the database is healthy.

### 6.5 A deploy succeeds but the app cannot start

- **What happens:** The build passes, but the running service crashes on boot (missing env var, bad config).
- **Why it matters:** A green build hides a red service.
- **Prevent:** A health-check route that exercises real dependencies (database reachable, Groq key present).
- **Detect:** Render and Vercel mark the deploy unhealthy when the health check fails.
- **Recover:** Automatic rollback; fix the config and redeploy.

### 6.6 The free or low tier sleeps, throttles, or hits a limit

- **What happens:** Render or Vercel free tiers spin down, cap build minutes, or limit bandwidth.
- **Why it matters:** Unexpected slowness or a hard stop at a bad moment.
- **Prevent:** Know each tier's limits; budget for an upgrade before launch; keep the backend warm if cold starts hurt UX.
- **Detect:** Latency and quota dashboards from each provider.
- **Recover:** Upgrade the tier; the configuration does not otherwise change.

---

## Cross-cutting concerns

These do not belong to a single phase - they touch the whole system.

### C.1 Time zones and "what counts as this week"

- **What happens:** Sources report timestamps in different time zones; the weekly cron runs in yet another.
- **Why it matters:** Posts land in the wrong week, smearing trend charts.
- **Prevent:** Store every timestamp in one standard zone (UTC) and convert only for display.
- **Detect:** Sanity-check counts at week boundaries.
- **Recover:** Re-bucket from the stored UTC timestamps - no re-collection needed.

### C.2 Personal information (PII) slips through

- **What happens:** A user writes their email, phone number, or full name inside a review.
- **Why it matters:** Storing or displaying it is a privacy and legal risk.
- **Prevent:** Scan and mask obvious PII during cleaning (Phase 2); never show raw contact details on the dashboard.
- **Detect:** A PII-pattern check in the cleaning report.
- **Recover:** Mask the affected records and re-publish the cleaned version.

### C.3 Total cost creeps across Groq, Supabase, Render, and Vercel

- **What happens:** Each service is individually cheap, but together they quietly grow with data volume and traffic.
- **Why it matters:** Surprise bills.
- **Prevent:** A simple monthly budget per service; per-run cost logging for Groq.
- **Detect:** Billing alerts on each provider.
- **Recover:** Sample data, cache results, or upgrade deliberately rather than by accident.

### C.4 Data integrity across the raw, clean, and insights layers

- **What happens:** The three layers fall out of sync (clean has rows raw does not, insights cite records that were re-cleaned away).
- **Why it matters:** Numbers stop adding up and trust erodes.
- **Prevent:** Always rebuild downstream layers from upstream ones, never edit a layer in place; keep IDs consistent across layers.
- **Detect:** Reconciliation checks comparing counts and ID coverage between layers.
- **Recover:** Rebuild the affected layer from the layer above it.

### C.5 No one owns a failure

- **What happens:** An alert fires at the weekend and everyone assumes someone else will handle it.
- **Why it matters:** Small problems grow into big gaps.
- **Prevent:** Name an owner for the pipeline and a simple on-call expectation; route all alerts to one place.
- **Detect:** An alert that is acknowledged, not just sent.
- **Recover:** Follow the break-glass runbook (rollback, rotate key, re-run synthesis) from Phase 6.

---

## Edge-case coverage map

A quick check that every part of [architecture.md](architecture.md) has its failure modes considered.

| Area | Covered cases |
|---|---|
| Setup guardrails (before we build) | S.1 |
| 1. Setup & Data Collection | 1.1 - 1.7 |
| 2. Storage, Standardization and Cleaning | 2.1 - 2.4 |
| 3. Insight Generation (SQL + Groq synthesis) | 3.1 - 3.7 |
| 4. Visualization and synthesis triggers | 4.1 - 4.6 |
| 5. Monitoring and Iteration | 5.1 - 5.3 |
| 6. Deployment, CI/CD and Fail-proofing | 6.1 - 6.6 |
| Cross-cutting (all phases) | C.1 - C.5 |

---

## Summary

The system is built to fail safely rather than to never fail. The recurring principles across every edge case are:

1. Keep the raw data untouched so any downstream step can be re-run.
2. Make runs resumable and window-based so a missed or partial run is automatically caught up.
3. Use a single writer (a lock) so the weekly job and the ad-hoc button never collide.
4. Anchor every Groq output to real counts and quotes so the model cannot mislead us.
5. Deploy through staging with health checks and automatic rollback so a bad release self-heals.
6. Keep secrets out of code, and name one owner who follows the break-glass runbook when something breaks.
