# Staging and production separation

Edge case **6.3**: staging and production must never share a database or cross API URLs.

## Recommended layout

| | Staging | Production |
|---|---------|------------|
| **Frontend** | Vercel project `nl-spotify-staging` | Vercel project `nl-spotify` |
| **Backend** | Render `nl-spotify-api-staging` | Render `nl-spotify-api` |
| **Supabase** | Separate project | Separate project |
| **APP_ENV** | `staging` | `production` |
| **Banner** | Yellow “Staging” banner | None |

## Environment variables

### Staging backend (Render)

```
APP_ENV=staging
EXPECTED_SUPABASE_PROJECT_REF=<staging-project-ref>
SUPABASE_PROJECT_URL=https://<staging-ref>.supabase.co
CORS_ORIGINS=https://nl-spotify-staging.vercel.app
```

### Production backend (Render)

```
APP_ENV=production
EXPECTED_SUPABASE_PROJECT_REF=<production-project-ref>
SUPABASE_PROJECT_URL=https://<production-ref>.supabase.co
CORS_ORIGINS=https://nl-spotify.vercel.app
```

### Staging frontend (Vercel)

```
NEXT_PUBLIC_APP_ENV=staging
NEXT_PUBLIC_API_URL=https://nl-spotify-api-staging.onrender.com
```

### Production frontend (Vercel)

```
NEXT_PUBLIC_APP_ENV=production
NEXT_PUBLIC_API_URL=https://nl-spotify-api.onrender.com
```

## Deploy flow

1. Merge to `main` → staging auto-deploys (Render + Vercel staging projects)
2. Run **Phase 6 deploy smoke** workflow against staging URL
3. **Promote** to production Vercel deployment when ready
4. Render production can auto-deploy from `main` or use manual promote — pick one policy and document it

## Validation

```bash
set APP_ENV=staging
set EXPECTED_SUPABASE_PROJECT_REF=your_staging_ref
python -m phase6_deploy.runner env-pairing
```

Backend `/health/ready` returns `503` if `EXPECTED_SUPABASE_PROJECT_REF` does not match the Supabase URL host.
