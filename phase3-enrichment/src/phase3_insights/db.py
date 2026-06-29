from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from supabase import Client, create_client
from postgrest.exceptions import APIError

from phase3_insights.config import Settings

PAGE_SIZE = 1000


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Database:
    def __init__(self, settings: Settings) -> None:
        self._client: Client = create_client(settings.supabase_url, settings.supabase_anon_key)
        self._clean = self._client.schema("clean")
        self._insights = self._client.schema("insights")

    def fetch_all_clean_items(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        offset = 0
        while True:
            response = (
                self._clean.table("feedback_items")
                .select("*")
                .range(offset, offset + PAGE_SIZE - 1)
                .execute()
            )
            batch = response.data or []
            if not batch:
                break
            items.extend(batch)
            if len(batch) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
        return items

    def get_daily_usage(self) -> tuple[int, int]:
        today_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
        response = (
            self._insights.table("synthesis_runs")
            .select("questions_answered, tokens_used")
            .gte("started_at", _iso(today_start))
            .execute()
        )
        rows = response.data or []
        requests = sum(int(r.get("questions_answered") or 0) for r in rows)
        # Executive summary counts as extra call; approximate via tokens / avg
        tokens = sum(int(r.get("tokens_used") or 0) for r in rows)
        return requests, tokens

    def start_run(self, metadata: dict | None = None) -> UUID:
        response = (
            self._insights.table("synthesis_runs")
            .insert({"status": "running", "metadata": metadata or {}})
            .execute()
        )
        return UUID(response.data[0]["id"])

    def finish_run(
        self,
        run_id: UUID,
        status: str,
        clean_items_analyzed: int,
        questions_answered: int,
        tokens_used: int,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        update: dict[str, Any] = {
            "status": status,
            "clean_items_analyzed": clean_items_analyzed,
            "questions_answered": questions_answered,
            "tokens_used": tokens_used,
            "error_message": error_message,
            "completed_at": _iso(utc_now()),
        }
        if metadata:
            update["metadata"] = metadata
        self._insights.table("synthesis_runs").update(update).eq("id", str(run_id)).execute()

    def save_question_answer(self, run_id: UUID, row: dict[str, Any]) -> None:
        row = dict(row)
        row["run_id"] = str(run_id)
        top_themes = row.pop("top_themes", None)
        stats = dict(row.get("stats") or {})
        if top_themes:
            stats["top_themes"] = top_themes
            row["stats"] = stats

        try:
            if top_themes is not None:
                row["top_themes"] = top_themes
            self._insights.table("question_answers").upsert(
                row,
                on_conflict="run_id,question_id",
            ).execute()
        except APIError as exc:
            message = str(exc)
            if top_themes is not None and "top_themes" in message:
                row.pop("top_themes", None)
                self._insights.table("question_answers").upsert(
                    row,
                    on_conflict="run_id,question_id",
                ).execute()
                return
            raise

    def save_executive_summary(self, run_id: UUID, row: dict[str, Any]) -> None:
        row["run_id"] = str(run_id)
        self._insights.table("executive_summary").upsert(
            row,
            on_conflict="run_id",
        ).execute()
