from __future__ import annotations

from datetime import datetime, timezone

from google_play_scraper import Sort, reviews
from google_play_scraper.exceptions import NotFoundError

from phase1_collection.collection_mode import CollectionMode
from phase1_collection.config import Settings
from phase1_collection.connectors.base import BaseConnector
from phase1_collection.db import RawFeedbackItem
from phase1_collection.validation import HealthCheckResult


class GooglePlayConnector(BaseConnector):
    source_name = "google_play"

    def __init__(self, settings: Settings) -> None:
        self._app_id = settings.spotify_play_store_id

    def collect(
        self,
        since: datetime,
        until: datetime,
        *,
        mode: CollectionMode = CollectionMode.WEEKLY,
    ) -> list[RawFeedbackItem]:
        items: list[RawFeedbackItem] = []
        continuation_token = None
        batches = 0

        while True:
            batches += 1
            if mode == CollectionMode.PROBE and batches > 1:
                break

            batch, continuation_token = reviews(
                self._app_id,
                lang="en",
                country="us",
                sort=Sort.NEWEST,
                count=100,
                continuation_token=continuation_token,
            )
            if not batch:
                break

            oldest_in_batch = None
            for review in batch:
                posted_at = review.get("at")
                if posted_at and posted_at.tzinfo is None:
                    posted_at = posted_at.replace(tzinfo=timezone.utc)
                if posted_at:
                    oldest_in_batch = posted_at if oldest_in_batch is None else min(oldest_in_batch, posted_at)

                if posted_at and posted_at < since:
                    continue
                if posted_at and posted_at > until:
                    continue

                review_id = review.get("reviewId")
                if not review_id:
                    continue

                text = review.get("content", "") or review.get("title", "")
                if not str(text).strip():
                    continue

                items.append(
                    self.normalize_item(
                        source_item_id=str(review_id),
                        posted_at=posted_at,
                        text=str(text),
                        extra={
                            "rating": review.get("score"),
                            "title": review.get("title"),
                            "user_name": review.get("userName"),
                            "thumbs_up": review.get("thumbsUpCount"),
                            "reply_content": review.get("replyContent"),
                        },
                    )
                )

            if oldest_in_batch and oldest_in_batch < since:
                break
            if not continuation_token:
                break

        return items

    def health_check(self) -> HealthCheckResult:
        try:
            batch, _ = reviews(self._app_id, count=1)
            if not batch:
                return HealthCheckResult(False, "Google Play returned no reviews")
            sample = batch[0]
            return HealthCheckResult(
                True,
                "Google Play scraper reachable",
                {"fields": list(sample.keys())},
            )
        except NotFoundError:
            return HealthCheckResult(False, f"Google Play app not found: {self._app_id}")
        except Exception as exc:  # noqa: BLE001
            return HealthCheckResult(False, f"Google Play health check failed: {exc}")
