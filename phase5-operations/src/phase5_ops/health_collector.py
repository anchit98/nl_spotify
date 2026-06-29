from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from phase5_ops.db import Database


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def collect_health_snapshot(db: Database, *, trigger: str = "manual") -> dict[str, Any]:
    """Build a point-in-time health snapshot from raw, clean, and insights tables."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    collection_runs = db.fetch_recent_collection_runs(limit=100)
    by_source: dict[str, dict[str, Any]] = {}
    collection_failures = 0

    for run in collection_runs:
        started = _parse_ts(run.get("started_at"))
        if started and started < week_ago:
            continue
        source = run.get("source") or "unknown"
        status = run.get("status")
        if status == "failed":
            collection_failures += 1
        items = int(run.get("items_collected") or 0)
        entry = by_source.setdefault(
            source,
            {"latest_status": None, "items_collected_7d": 0, "runs_7d": 0},
        )
        if entry["latest_status"] is None:
            entry["latest_status"] = status
        entry["items_collected_7d"] += items
        entry["runs_7d"] += 1

    clean_total, rated_total = db.count_clean_items()
    synthesis_runs = db.fetch_recent_synthesis_runs(limit=5)
    latest = synthesis_runs[0] if synthesis_runs else None

    model = None
    if latest:
        meta = latest.get("metadata") or {}
        model = meta.get("model")

    snapshot = {
        "trigger": trigger,
        "corpus_clean_total": clean_total,
        "corpus_rated_total": rated_total,
        "collection_by_source": by_source,
        "collection_failures": collection_failures,
        "latest_synthesis_run_id": latest.get("id") if latest else None,
        "synthesis_status": latest.get("status") if latest else None,
        "synthesis_questions_answered": int(latest.get("questions_answered") or 0) if latest else None,
        "synthesis_tokens_used": int(latest.get("tokens_used") or 0) if latest else None,
        "synthesis_model": model,
        "metrics": {
            "synthesis_runs_in_db": len(synthesis_runs),
            "collection_sources_active_7d": len(by_source),
        },
    }
    return snapshot
