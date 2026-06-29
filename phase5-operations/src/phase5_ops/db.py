from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from supabase import Client, create_client

from phase5_ops.config import Settings

PAGE_SIZE = 1000


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat()


class Database:
    def __init__(self, settings: Settings) -> None:
        self._client: Client = create_client(settings.supabase_url, settings.supabase_anon_key)
        self._raw = self._client.schema("raw")
        self._clean = self._client.schema("clean")
        self._insights = self._client.schema("insights")
        self._ops = self._client.schema("ops")

    def fetch_recent_collection_runs(self, *, limit: int = 50) -> list[dict[str, Any]]:
        response = (
            self._raw.table("collection_runs")
            .select("*")
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def count_clean_items(self) -> tuple[int, int]:
        total = 0
        rated = 0
        offset = 0
        while True:
            response = (
                self._clean.table("feedback_items")
                .select("rating")
                .range(offset, offset + PAGE_SIZE - 1)
                .execute()
            )
            batch = response.data or []
            if not batch:
                break
            total += len(batch)
            rated += sum(1 for row in batch if row.get("rating") is not None)
            if len(batch) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
        return total, rated

    def fetch_recent_synthesis_runs(self, *, limit: int = 20) -> list[dict[str, Any]]:
        response = (
            self._insights.table("synthesis_runs")
            .select("*")
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def fetch_question_answers(self, run_id: str) -> list[dict[str, Any]]:
        response = (
            self._insights.table("question_answers")
            .select("question_id, top_themes, stats, model_version")
            .eq("run_id", run_id)
            .execute()
        )
        return response.data or []

    def has_executive_summary(self, run_id: str) -> bool:
        response = (
            self._insights.table("executive_summary")
            .select("id")
            .eq("run_id", run_id)
            .limit(1)
            .execute()
        )
        return bool(response.data)

    def save_health_snapshot(self, row: dict[str, Any]) -> UUID:
        response = self._ops.table("health_snapshots").insert(row).execute()
        return UUID(response.data[0]["id"])

    def fetch_health_snapshots(self, *, limit: int = 12) -> list[dict[str, Any]]:
        response = (
            self._ops.table("health_snapshots")
            .select("*")
            .order("captured_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def upsert_theme_trends(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        self._ops.table("theme_trends").upsert(rows, on_conflict="synthesis_run_id,question_id,theme").execute()

    def fetch_theme_trends_for_run(self, run_id: str) -> list[dict[str, Any]]:
        response = (
            self._ops.table("theme_trends")
            .select("*")
            .eq("synthesis_run_id", run_id)
            .execute()
        )
        return response.data or []

    def save_alert(self, row: dict[str, Any]) -> UUID:
        response = self._ops.table("alerts").insert(row).execute()
        return UUID(response.data[0]["id"])

    def mark_alert_notified(self, alert_id: UUID) -> None:
        self._ops.table("alerts").update({"notified": True}).eq("id", str(alert_id)).execute()

    def recent_alert_exists(self, category: str, title: str, *, hours: int = 24) -> bool:
        since = utc_now().replace(microsecond=0)
        from datetime import timedelta

        cutoff = (since - timedelta(hours=hours)).isoformat()
        response = (
            self._ops.table("alerts")
            .select("id")
            .eq("category", category)
            .eq("title", title)
            .gte("fired_at", cutoff)
            .limit(1)
            .execute()
        )
        return bool(response.data)

    def record_model_pin(self, groq_model: str, prompt_version: str, notes: str | None = None) -> None:
        self._ops.table("model_registry").upsert(
            {
                "groq_model": groq_model,
                "prompt_version": prompt_version,
                "notes": notes,
                "recorded_at": _iso(utc_now()),
            },
            on_conflict="groq_model,prompt_version",
        ).execute()

    def latest_model_pin(self) -> dict[str, Any] | None:
        response = (
            self._ops.table("model_registry")
            .select("*")
            .order("recorded_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def list_open_review_actions(self) -> list[dict[str, Any]]:
        response = (
            self._ops.table("review_actions")
            .select("*")
            .in_("status", ["open", "in_progress"])
            .order("review_date", desc=True)
            .execute()
        )
        return response.data or []
