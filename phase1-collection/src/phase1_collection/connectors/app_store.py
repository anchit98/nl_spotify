from __future__ import annotations

from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from phase1_collection.collection_mode import CollectionMode
from phase1_collection.config import Settings
from phase1_collection.connectors.base import BaseConnector
from phase1_collection.db import RawFeedbackItem
from phase1_collection.validation import HealthCheckResult


def _parse_rfc822(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        from email.utils import parsedate_to_datetime

        return parsedate_to_datetime(value).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


class AppStoreConnector(BaseConnector):
    source_name = "app_store"

    def __init__(self, settings: Settings) -> None:
        self._app_id = settings.spotify_app_store_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def _fetch_page(self, page: int) -> dict:
        url = (
            f"https://itunes.apple.com/rss/customerreviews/page={page}/id={self._app_id}"
            "/sortby=mostrecent/json"
        )
        response = httpx.get(url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        return response.json()

    def collect(
        self,
        since: datetime,
        until: datetime,
        *,
        mode: CollectionMode = CollectionMode.WEEKLY,
    ) -> list[RawFeedbackItem]:
        items: list[RawFeedbackItem] = []
        page = 0

        while True:
            page += 1
            if mode == CollectionMode.PROBE and page > 1:
                break

            data = self._fetch_page(page)
            entries = data.get("feed", {}).get("entry", [])
            if not entries:
                break
            if isinstance(entries, dict):
                entries = [entries]

            page_in_window = False
            all_older_than_since = True
            for entry in entries:
                if "im:rating" not in entry:
                    continue

                posted_at = _parse_rfc822(entry.get("updated", {}).get("label"))
                if posted_at and posted_at >= since:
                    all_older_than_since = False
                if posted_at and posted_at < since:
                    continue
                if posted_at and posted_at > until:
                    continue

                review_id = entry.get("id", {}).get("label") or entry.get("id", {}).get("attributes", {}).get("im:id")
                if not review_id:
                    continue

                text = entry.get("content", {}).get("label", "")
                title = entry.get("title", {}).get("label", "")
                rating = entry.get("im:rating", {}).get("label")

                items.append(
                    self.normalize_item(
                        source_item_id=str(review_id),
                        posted_at=posted_at,
                        text=text or title,
                        extra={
                            "title": title,
                            "rating": rating,
                            "author": entry.get("author", {}).get("name", {}).get("label"),
                        },
                    )
                )
                page_in_window = True

            if all_older_than_since and page > 1:
                break
            if not page_in_window and page > 1:
                break

        return items

    def health_check(self) -> HealthCheckResult:
        try:
            data = self._fetch_page(1)
            feed = data.get("feed", {})
            if "entry" not in feed:
                return HealthCheckResult(False, "No entries in App Store RSS feed")
            return HealthCheckResult(True, "App Store RSS reachable", {"keys": list(feed.keys())})
        except Exception as exc:  # noqa: BLE001
            return HealthCheckResult(False, f"App Store health check failed: {exc}")
