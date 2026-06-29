# Phase 6: Deployment, CI/CD and Fail-proofing

Implements [architecture.md](../docs/architecture.md) Phase 6 and [edgecases.md](../docs/edgecases.md) §6.1–6.6 in a standalone package.

## What this phase delivers

| Output | Location |
|--------|----------|
| Secret scanning (6.2) | `phase6_deploy secret-scan` |
| Migration manifest + dry-run (6.4) | `config/migrations.manifest.yaml`, `migrations-dry-run` |
| Staging/production pairing (6.3) | `env-pairing`, backend `APP_ENV`, frontend banner |
| Deep health check (6.5) | Backend `GET /health/ready` |
| Groq CI smoke test (6.1) | `groq-smoke` |
| Post-deploy smoke | `deploy-smoke` |
| Layer reconciliation (C.4) | `reconcile` |
| Break-glass runbook | [docs/break-glass-runbook.md](docs/break-glass-runbook.md) |
| Branch protection guide | [docs/branch-protection.md](docs/branch-protection.md) |
| Staging Render blueprint | [config/render-staging.yaml](config/render-staging.yaml) |

## Setup

```bash
cd phase6-deploy
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## CLI

```bash
set PYTHONPATH=src

# All PR-safe checks (no live Groq call)
python -m phase6_deploy.runner ci

# Individual commands
python -m phase6_deploy.runner secret-scan
python -m phase6_deploy.runner migrations-validate
python -m phase6_deploy.runner migrations-dry-run
python -m phase6_deploy.runner env-pairing
python -m phase6_deploy.runner groq-smoke
python -m phase6_deploy.runner deploy-smoke
python -m phase6_deploy.runner reconcile
```

## GitHub Actions

| Workflow | Purpose |
|----------|---------|
| [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | Lint, build, Phase 6 `ci` + optional Groq smoke on `main` |
| [`.github/workflows/phase6-secret-scan.yml`](../.github/workflows/phase6-secret-scan.yml) | Secret scan on every PR |
| [`.github/workflows/phase6-deploy-smoke.yml`](../.github/workflows/phase6-deploy-smoke.yml) | Manual post-deploy smoke |

## Backend / frontend integration

- **Render** health check → `/health/ready` (validates Supabase + Groq key + env pairing)
- **Backend env:** `APP_ENV`, `EXPECTED_SUPABASE_PROJECT_REF`
- **Frontend env:** `NEXT_PUBLIC_APP_ENV` — non-production shows a staging banner

## Staging vs production

See [docs/staging-production.md](docs/staging-production.md). Use **separate Supabase projects** and [config/render-staging.yaml](config/render-staging.yaml).

## Emergencies

See [docs/break-glass-runbook.md](docs/break-glass-runbook.md).
