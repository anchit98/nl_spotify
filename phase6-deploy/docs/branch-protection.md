# GitHub branch protection setup

Implements architecture Phase 6: **nothing merges to `main` without review and green CI** (edge case 6.1).

## Steps (repo admin)

1. GitHub → **Settings → Branches → Add branch protection rule**
2. Branch name pattern: `main`
3. Enable:
   - [x] **Require a pull request before merging**
   - [x] **Require approvals** (1 minimum)
   - [x] **Require status checks to pass before merging**
   - [x] **Require branches to be up to date before merging**
4. Search and select required checks:
   - `Frontend lint & build`
   - `Backend import check`
   - `Phase 6 CI checks`
   - `Secret scan`
5. Enable **Do not allow bypassing the above settings** (recommended)

## Optional

- **Require conversation resolution** before merge
- **Include administrators** if the whole team must follow the same rules
- Enable **GitHub Advanced Security → Secret scanning** if available on your plan

## Developer workflow

```text
feature branch → open PR → CI green → review → merge → Render + Vercel auto-deploy
```

## Groq smoke on `main` only

The Groq smoke test uses a real API call and runs on pushes to `main` (not every PR) to conserve quota. PRs still run secret scan, migration validate, lint, and build.
