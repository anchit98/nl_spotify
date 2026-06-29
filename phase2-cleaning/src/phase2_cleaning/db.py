from datetime import datetime, timezone
from typing import Any
from uuid import UUID
from supabase import Client, ClientOptions, create_client
from phase2_cleaning.config import Settings

def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat()

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Database:
    def __init__(self, settings: Settings) -> None:
        # Supabase defaults to the "public" schema for RPC calls if not specified.
        # We need to specify the schema for the client.
        options = ClientOptions(schema="clean")
        self._client: Client = create_client(settings.supabase_url, settings.supabase_anon_key, options=options)
        self._clean = self._client.schema("clean")

    def get_unprocessed_raw_items(self, batch_size: int = 1000) -> list[dict[str, Any]]:
        response = self._client.rpc("get_unprocessed_raw_items", {"batch_size": batch_size}).execute()
        return response.data or []

    def start_run(self) -> UUID:
        response = (
            self._clean.table("cleaning_runs")
            .insert({"status": "running"})
            .execute()
        )
        return UUID(response.data[0]["id"])

    def finish_run(
        self,
        run_id: UUID,
        status: str,
        items_processed: int,
        items_kept: int,
        error_message: str | None = None,
    ) -> None:
        self._clean.table("cleaning_runs").update(
            {
                "status": status,
                "items_processed": items_processed,
                "items_kept": items_kept,
                "error_message": error_message,
                "completed_at": _iso(utc_now()),
            }
        ).eq("id", str(run_id)).execute()

    def save_cleaned_items(
        self,
        kept_items: list[dict[str, Any]],
        processed_records: list[dict[str, Any]]
    ) -> None:
        # Insert into clean.feedback_items
        if kept_items:
            # Batch inserts
            chunk_size = 100
            for i in range(0, len(kept_items), chunk_size):
                chunk = kept_items[i : i + chunk_size]
                self._clean.table("feedback_items").upsert(
                    chunk,
                    on_conflict="source,source_item_id",
                    ignore_duplicates=True,
                ).execute()

        # Insert into clean.processed_raw_items
        if processed_records:
            chunk_size = 100
            for i in range(0, len(processed_records), chunk_size):
                chunk = processed_records[i : i + chunk_size]
                self._clean.table("processed_raw_items").upsert(
                    chunk,
                    on_conflict="raw_id",
                    ignore_duplicates=True,
                ).execute()
