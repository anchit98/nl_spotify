from __future__ import annotations

from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from phase1_collection.collection_mode import CollectionMode
from phase1_collection.config import Settings
from phase1_collection.connectors.base import BaseConnector
from phase1_collection.db import RawFeedbackItem
from phase1_collection.validation import HealthCheckResult

PULLPUSH_BASE = "https://api.pullpush.io/reddit/search"
SUBREDDITS = ("spotify", "truespotify", "spotifyplaylists")
SEARCH_QUERIES = (
    "discovery recommendations",
    "discover weekly",
    "repetitive recommendations",
)
PAGE_SIZE = 100
PROBE_SIZE = 25


class RedditConnector(BaseConnector):
    """Public Reddit archive search via PullPush (no API keys)."""

    source_name = "reddit"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def _fetch(self, kind: str, params: dict) -> list[dict]:
        response = httpx.get(f"{PULLPUSH_BASE}/{kind}/", params=params, timeout=60.0)
        response.raise_for_status()
        return response.json().get("data", [])

    def _to_item(self, record: dict, *, kind: str, extra: dict | None = None) -> RawFeedbackItem | None:
        text = record.get("selftext") or record.get("body") or record.get("title") or ""
        if not str(text).strip():
            return None

        created = record.get("created_utc")
        posted_at = datetime.fromtimestamp(created, tz=timezone.utc) if created else None
        item_id = record.get("id")
        if not item_id:
            return None

        prefix = "comment" if kind == "comment" else "submission"
        return self.normalize_item(
            source_item_id=f"{prefix}:{item_id}",
            posted_at=posted_at,
            text=str(text),
            extra={
                "kind": kind,
                "subreddit": record.get("subreddit"),
                "title": record.get("title"),
                "url": record.get("permalink") or record.get("url"),
                "score": record.get("score"),
                **(extra or {}),
            },
        )

    def _fetch_paginated(
        self,
        kind: str,
        base_params: dict,
        since: datetime,
        until: datetime,
        *,
        mode: CollectionMode,
    ) -> list[RawFeedbackItem]:
        items: list[RawFeedbackItem] = []
        seen: set[str] = set()
        size = PROBE_SIZE if mode == CollectionMode.PROBE else PAGE_SIZE
        params = {**base_params, "size": size, "after": int(since.timestamp())}
        before: int | None = None
        pages = 0

        while True:
            pages += 1
            if mode == CollectionMode.PROBE and pages > 1:
                break

            page_params = dict(params)
            if before is not None:
                page_params["before"] = before

            records = self._fetch(kind, page_params)
            if not records:
                break

            oldest_ts: int | None = None
            for record in records:
                created = record.get("created_utc")
                if created is not None:
                    oldest_ts = created if oldest_ts is None else min(oldest_ts, created)

                item = self._to_item(record, kind=kind)
                if not item or item.source_item_id in seen:
                    continue
                if item.posted_at and (item.posted_at < since or item.posted_at > until):
                    continue
                seen.add(item.source_item_id)
                items.append(item)

            if oldest_ts is None or oldest_ts < int(since.timestamp()):
                break
            if len(records) < size:
                break
            before = oldest_ts

        return items

    def _subreddit_items(
        self,
        since: datetime,
        until: datetime,
        *,
        mode: CollectionMode,
    ) -> list[RawFeedbackItem]:
        items: list[RawFeedbackItem] = []
        subs = SUBREDDITS[:1] if mode == CollectionMode.PROBE else SUBREDDITS

        for sub in subs:
            items.extend(
                self._fetch_paginated(
                    "submission",
                    {"subreddit": sub},
                    since,
                    until,
                    mode=mode,
                )
            )
        return items

    def _search_items(
        self,
        since: datetime,
        until: datetime,
        *,
        mode: CollectionMode,
    ) -> list[RawFeedbackItem]:
        items: list[RawFeedbackItem] = []
        queries = SEARCH_QUERIES[:1] if mode == CollectionMode.PROBE else SEARCH_QUERIES

        for query in queries:
            batch = self._fetch_paginated(
                "submission",
                {"q": query},
                since,
                until,
                mode=mode,
            )
            for item in batch:
                item.raw_payload["query"] = query
                items.append(item)
        return items

    def _collect_unfiltered(self, *, mode: CollectionMode) -> list[RawFeedbackItem]:
        """Fallback when archive posts fall outside the requested window (initial mode only)."""
        items: list[RawFeedbackItem] = []
        size = PROBE_SIZE if mode == CollectionMode.PROBE else PAGE_SIZE
        subs = SUBREDDITS[:1] if mode == CollectionMode.PROBE else SUBREDDITS
        for sub in subs:
            for record in self._fetch("submission", {"subreddit": sub, "size": size}):
                item = self._to_item(record, kind="submission", extra={"archive_outside_window": True})
                if item:
                    items.append(item)
        return items

    def collect(
        self,
        since: datetime,
        until: datetime,
        *,
        mode: CollectionMode = CollectionMode.WEEKLY,
    ) -> list[RawFeedbackItem]:
        items = self._subreddit_items(since, until, mode=mode)
        items.extend(self._search_items(since, until, mode=mode))
        if not items and mode == CollectionMode.INITIAL:
            items = self._collect_unfiltered(mode=mode)
        return items

    def health_check(self) -> HealthCheckResult:
        try:
            data = self._fetch("submission", {"subreddit": "spotify", "size": 1})
            if not data:
                return HealthCheckResult(False, "PullPush returned no Reddit posts")
            return HealthCheckResult(True, "PullPush Reddit archive reachable")
        except Exception as exc:  # noqa: BLE001
            return HealthCheckResult(False, f"Reddit health check failed: {exc}")
