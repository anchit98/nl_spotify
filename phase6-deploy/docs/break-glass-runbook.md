# Break-glass runbook

Use when production is broken, secrets leak, or the pipeline fails over a weekend (edge cases 6.1–6.2, C.5).

## 1. Roll back a bad deploy

### Render (backend)

1. Render Dashboard → **nl-spotify-api** → **Events**
2. Find the last **successful** deploy before the incident
3. **Rollback** to that deploy
4. Verify: `curl https://YOUR-API.onrender.com/health/ready`

### Vercel (frontend)

1. Vercel Dashboard → project → **Deployments**
2. Open the last known-good deployment → **⋯** → **Promote to Production**
3. Hard-refresh the site (Ctrl+Shift+R)

> Never `git push --force` to `main` to roll back. Redeploy a known-good commit instead.

## 2. Rotate a leaked Groq API key

1. [Groq Console](https://console.groq.com) → revoke the exposed key immediately
2. Create a new key
3. Update in **all** places:
   - GitHub Actions secrets (`GROQ_API_KEY`)
   - Render env (production + staging)
   - Local `.env` (not committed)
4. Redeploy backend (or restart Render service)
5. Run `python -m phase6_deploy.runner groq-smoke` locally to confirm

If the key was committed to GitHub, also:

- Run `python -m phase6_deploy.runner secret-scan` after removal
- Consider `git filter-repo` or GitHub secret scanning remediation
- Open an incident note in your team channel

## 3. Rotate Supabase credentials

1. Supabase Dashboard → **Settings → API**
2. Roll **anon** key if exposed (or create a new project for staging crossover incidents)
3. Update Render, Vercel, GitHub Actions secrets
4. Run `python -m phase6_deploy.runner migrations-dry-run`

## 4. Re-run a failed weekly synthesis

### Option A — GitHub Actions (preferred)

1. **Actions → Data Pipeline (Phases 1-3) → Run workflow**
2. Mode: `weekly` (or `adhoc` for last 7 days only)
3. Watch **Phase 5 Monitor** workflow after success

### Option B — Dashboard button

1. Open production/staging dashboard → **Synthesize now**
2. Monitor `/synthesis` page
3. **Note:** Groq free tier ~100k tokens/day — avoid multiple full runs same day

### Option C — Local

```bash
cd phase3-enrichment
set PYTHONPATH=src
python -m phase3_insights.synthesizer
```

## 5. Pipeline red — quick triage

| Symptom | First check |
|---------|-------------|
| Collection failed | `raw.collection_runs` latest rows; connector health in Actions log |
| Cleaning failed | Phase 2 log; unprocessed raw backlog |
| Synthesis failed | Groq quota; `insights.synthesis_runs.error_message` |
| Deploy unhealthy | `/health/ready` response body; missing env var on Render |
| CORS / blank UI | `CORS_ORIGINS`, `NEXT_PUBLIC_API_URL` pairing |

## 6. Staging crossed with production (6.3)

1. Check `APP_ENV` on Render and `NEXT_PUBLIC_APP_ENV` on Vercel
2. Verify `EXPECTED_SUPABASE_PROJECT_REF` matches Supabase URL host
3. Fix env vars → redeploy both services
4. Run `python -m phase6_deploy.runner env-pairing`

## 7. Who owns the incident

- **Pipeline failures:** data engineer
- **Deploy / outage:** backend + frontend owner
- **Product-facing wrong insights:** product lead + pause dashboard link until synthesis re-run

Acknowledge Phase 5 alerts in `ops.alerts` (`acknowledged_at`) after handling.

## 8. After recovery

- [ ] `/health/ready` returns 200
- [ ] Home page loads with executive summary
- [ ] `phase6_deploy.runner deploy-smoke` passes
- [ ] Post-mortem: update thresholds in `phase5-operations/config/alert_thresholds.yaml` if needed
