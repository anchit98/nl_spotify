from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from supabase import Client, create_client

from phase1_collection.config import Settings, utc_now


@dataclass(frozen=True)
class RawFeedbackItem:
    source_item_id: str
    posted_at: datetime | None
    raw_payload: dict[str, Any]


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone().isoformat()


class Database:
    """Supabase REST client for the raw schema (no direct Postgres URL required)."""

    def __init__(self, settings: Settings) -> None:
        self._client: Client = create_client(settings.supabase_url, settings.supabase_anon_key)
        self._raw = self._client.schema("raw")

    def get_window_start(self, source: str, fallback: datetime) -> datetime:
        response = (
            self._raw.table("collection_runs")
            .select("window_end")
            .eq("source", source)
            .eq("status", "success")
            .gt("items_collected", 0)
            .order("completed_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if rows and rows[0].get("window_end"):
            return datetime.fromisoformat(rows[0]["window_end"].replace("Z", "+00:00"))
        return fallback

    def start_run(self, source: str, window_start: datetime, window_end: datetime) -> UUID:
        response = (
            self._raw.table("collection_runs")
            .insert(
                {
                    "source": source,
                    "status": "running",
                    "window_start": _iso(window_start),
                    "window_end": _iso(window_end),
                }
            )
            .execute()
        )
        return UUID(response.data[0]["id"])

    def finish_run(
        self,
        run_id: UUID,
        status: str,
        items_collected: int,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        existing = (
            self._raw.table("collection_runs")
            .select("metadata")
            .eq("id", str(run_id))
            .single()
            .execute()
        )
        merged_meta = {**(existing.data.get("metadata") or {}), **(metadata or {})}
        self._raw.table("collection_runs").update(
            {
                "status": status,
                "items_collected": items_collected,
                "error_message": error_message,
                "metadata": merged_meta,
                "completed_at": _iso(utc_now()),
            }
        ).eq("id", str(run_id)).execute()

    def upsert_items(self, source: str, run_id: UUID, items: list[RawFeedbackItem]) -> int:
        if not items:
            return 0

        before = self.count_items(source)
        rows = [
            {
                "source": source,
                "source_item_id": item.source_item_id,
                "run_id": str(run_id),
                "posted_at": _iso(item.posted_at),
                "raw_payload": item.raw_payload,
            }
            for item in items
        ]

        # Batch in chunks to avoid payload limits
        chunk_size = 100
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            self._raw.table("feedback_items").upsert(
                chunk,
                on_conflict="source,source_item_id",
                ignore_duplicates=True,
            ).execute()

        after = self.count_items(source)
        return max(after - before, 0)

    def count_items(self, source: str | None = None) -> int:
        query = self._raw.table("feedback_items").select("id", count="exact")
        if source:
            query = query.eq("source", source)
        response = query.execute()
        return int(response.count or 0)

    def latest_run_age_days(self) -> float | None:
        response = (
            self._raw.table("collection_runs")
            .select("completed_at")
            .eq("status", "success")
            .order("completed_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows or not rows[0].get("completed_at"):
            return None
        completed = datetime.fromisoformat(rows[0]["completed_at"].replace("Z", "+00:00"))
        delta = datetime.now(completed.tzinfo) - completed
        return delta.total_seconds() / 86400.0
