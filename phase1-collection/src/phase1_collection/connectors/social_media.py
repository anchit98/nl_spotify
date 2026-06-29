from __future__ import annotations

from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from phase1_collection.collection_mode import CollectionMode
from phase1_collection.config import Settings
from phase1_collection.connectors.base import BaseConnector
from phase1_collection.db import RawFeedbackItem
from phase1_collection.validation import HealthCheckResult

# Public Mastodon tag timelines — no API keys.
INSTANCES = ("mastodon.social", "mastodon.online")
TAGS = ("spotify", "spotifyplaylist", "musicdiscovery")
PAGE_LIMIT = 40
PROBE_LIMIT = 10


class SocialMediaConnector(BaseConnector):
    source_name = "social_media"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def _fetch_tag(self, instance: str, tag: str, *, limit: int, max_id: str | None = None) -> list[dict]:
        url = f"https://{instance}/api/v1/timelines/tag/{tag}"
        params: dict[str, str | int] = {"limit": limit}
        if max_id:
            params["max_id"] = max_id
        response = httpx.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _strip_html(html: str) -> str:
        return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)

    def _collect_tag(
        self,
        instance: str,
        tag: str,
        since: datetime,
        until: datetime,
        *,
        mode: CollectionMode,
        seen: set[str],
    ) -> list[RawFeedbackItem]:
        items: list[RawFeedbackItem] = []
        limit = PROBE_LIMIT if mode == CollectionMode.PROBE else PAGE_LIMIT
        max_id: str | None = None
        pages = 0

        while True:
            pages += 1
            if mode == CollectionMode.PROBE and pages > 1:
                break

            statuses = self._fetch_tag(instance, tag, limit=limit, max_id=max_id)
            if not statuses:
                break

            oldest_in_page: datetime | None = None
            for status in statuses:
                status_id = str(status.get("id", ""))
                if not status_id or status_id in seen:
                    continue

                posted_at = None
                if status.get("created_at"):
                    posted_at = datetime.fromisoformat(status["created_at"].replace("Z", "+00:00"))
                if posted_at:
                    oldest_in_page = posted_at if oldest_in_page is None else min(oldest_in_page, posted_at)

                if posted_at and (posted_at < since or posted_at > until):
                    continue

                text = self._strip_html(status.get("content", ""))
                if not text.strip():
                    continue

                seen.add(status_id)
                account = status.get("account", {})
                items.append(
                    self.normalize_item(
                        source_item_id=f"{instance}:{status_id}",
                        posted_at=posted_at,
                        text=text,
                        extra={
                            "platform": "mastodon",
                            "instance": instance,
                            "tag": tag,
                            "author_handle": account.get("acct"),
                            "favourites": status.get("favourites_count"),
                            "url": status.get("url"),
                        },
                    )
                )

            if oldest_in_page and oldest_in_page < since:
                break
            if len(statuses) < limit:
                break
            max_id = str(statuses[-1]["id"])

        return items

    def collect(
        self,
        since: datetime,
        until: datetime,
        *,
        mode: CollectionMode = CollectionMode.WEEKLY,
    ) -> list[RawFeedbackItem]:
        items: list[RawFeedbackItem] = []
        seen: set[str] = set()
        tags = TAGS[:1] if mode == CollectionMode.PROBE else TAGS
        instances = INSTANCES[:1] if mode == CollectionMode.PROBE else INSTANCES

        for instance in instances:
            for tag in tags:
                items.extend(
                    self._collect_tag(instance, tag, since, until, mode=mode, seen=seen)
                )
        return items

    def health_check(self) -> HealthCheckResult:
        try:
            data = self._fetch_tag(INSTANCES[0], "spotify", limit=1)
            if not data:
                return HealthCheckResult(False, "Mastodon tag timeline returned no posts")
            return HealthCheckResult(True, "Mastodon public timeline reachable")
        except Exception as exc:  # noqa: BLE001
            return HealthCheckResult(False, f"Social media health check failed: {exc}")
