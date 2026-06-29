from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from phase1_collection.collection_mode import CollectionMode
from phase1_collection.config import Settings
from phase1_collection.connectors.base import BaseConnector
from phase1_collection.db import RawFeedbackItem
from phase1_collection.validation import HealthCheckResult

SEARCH_TERMS = (
    "discover weekly",
    "recommendations",
    "discovery",
)


class CommunityForumConnector(BaseConnector):
    """Scrapes public Spotify Community search results (isolated; may break on layout changes)."""

    source_name = "community_forum"
    base_url = "https://community.spotify.com"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
        }

    def _search_url(self, term: str, page: int = 1) -> str:
        return (
            f"{self.base_url}/t5/forums/searchpage/tab/message"
            f"?filter=location&location=category:en_spotify&query={quote_plus(term)}&page={page}"
        )

    def _parse_results(self, html: str, since: datetime, until: datetime) -> list[RawFeedbackItem]:
        soup = BeautifulSoup(html, "html.parser")
        items: list[RawFeedbackItem] = []
        seen: set[str] = set()

        for link in soup.select("a[href*='/td-p/']"):
            href = link.get("href", "")
            title = link.get_text(strip=True)
            if not href or not title or href in seen:
                continue
            seen.add(href)

            item_id = href.rstrip("/").split("/")[-1]
            items.append(
                self.normalize_item(
                    source_item_id=f"thread:{item_id}",
                    posted_at=None,
                    text=title,
                    extra={
                        "url": href if href.startswith("http") else f"{self.base_url}{href}",
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
            )

        filtered: list[RawFeedbackItem] = []
        for item in items:
            if item.posted_at is None:
                filtered.append(item)
            elif since <= item.posted_at <= until:
                filtered.append(item)
        return filtered

    def collect(
        self,
        since: datetime,
        until: datetime,
        *,
        mode: CollectionMode = CollectionMode.WEEKLY,
    ) -> list[RawFeedbackItem]:
        items: list[RawFeedbackItem] = []
        seen_ids: set[str] = set()
        terms = SEARCH_TERMS[:1] if mode == CollectionMode.PROBE else SEARCH_TERMS

        with httpx.Client(timeout=30.0, follow_redirects=True, headers=self._headers) as client:
            for term in terms:
                page = 0
                while True:
                    page += 1
                    if mode == CollectionMode.PROBE and page > 1:
                        break

                    response = client.get(self._search_url(term, page=page))
                    response.raise_for_status()
                    page_items = self._parse_results(response.text, since, until)
                    new_items = [item for item in page_items if item.source_item_id not in seen_ids]
                    if not new_items:
                        break
                    for item in new_items:
                        seen_ids.add(item.source_item_id)
                    items.extend(new_items)

        return items

    def health_check(self) -> HealthCheckResult:
        try:
            response = httpx.get(
                self._search_url("spotify"),
                timeout=30.0,
                follow_redirects=True,
                headers=self._headers,
            )
            response.raise_for_status()
            if "lia-" not in response.text and "community" not in response.text.lower():
                return HealthCheckResult(False, "Community forum HTML layout unexpected")
            return HealthCheckResult(True, "Community forum search reachable")
        except Exception as exc:  # noqa: BLE001
            return HealthCheckResult(False, f"Community forum health check failed: {exc}")
