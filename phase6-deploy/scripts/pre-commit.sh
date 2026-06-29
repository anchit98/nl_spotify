#!/usr/bin/env bash
# Optional local pre-commit hook (edge case 6.2). Install:
#   cp phase6-deploy/scripts/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
export PYTHONPATH="$ROOT/phase6-deploy/src"

if [ -f "$ROOT/phase6-deploy/.venv/bin/python" ]; then
  PY="$ROOT/phase6-deploy/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  PY=python
fi

echo "Phase 6 secret scan..."
"$PY" -m phase6_deploy.runner secret-scan
