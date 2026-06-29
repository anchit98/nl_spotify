from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from supabase import create_client

from phase6_deploy.config import Settings


def load_manifest(phase6_root: Path) -> list[dict[str, Any]]:
    path = phase6_root / "config" / "migrations.manifest.yaml"
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return list(data.get("migrations") or [])


def validate_manifest(repo_root: Path, phase6_root: Path) -> list[str]:
    """Ensure every migration file exists on disk (dry-run before deploy)."""
    errors: list[str] = []
    for entry in load_manifest(phase6_root):
        rel = entry.get("path")
        if not rel:
            errors.append(f"Migration missing path: {entry}")
            continue
        full = repo_root / rel
        if not full.is_file():
            errors.append(f"Migration file not found: {rel}")
        elif full.stat().st_size == 0:
            errors.append(f"Migration file is empty: {rel}")
    return errors


def verify_schemas_reachable(settings: Settings, phase6_root: Path) -> list[str]:
    """Best-effort live check that expected schemas respond via Supabase REST."""
    if not settings.supabase_url or not settings.supabase_anon_key:
        return ["Cannot verify schemas: Supabase credentials missing"]

    errors: list[str] = []
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    probes = {
        "raw": ("collection_runs", client.schema("raw")),
        "clean": ("feedback_items", client.schema("clean")),
        "insights": ("synthesis_runs", client.schema("insights")),
        "ops": ("health_snapshots", client.schema("ops")),
    }
    for schema, (table, schema_client) in probes.items():
        try:
            schema_client.table(table).select("id").limit(1).execute()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Schema '{schema}' not reachable ({table}): {exc}")
    return errors
