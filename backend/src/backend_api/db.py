from __future__ import annotations

import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from supabase import Client, create_client

from backend_api.config import Settings

PAGE_SIZE = 1000
_DATASET_STATS_CACHE: tuple[float, dict[str, Any]] | None = None
_DATASET_STATS_TTL_SECONDS = 60
_CLEAN_ITEMS_CACHE: tuple[float, list[dict[str, Any]]] | None = None
_BUNDLES_CACHE: tuple[float, dict[str, Any]] | None = None
_REVIEW_TRENDS_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}

TREND_GRANULARITIES = frozenset({"week", "month", "year"})
TRENDS_CHART_START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def clear_response_caches() -> None:
    """Drop in-memory API caches so the next read reflects new synthesis or data."""
    global _DATASET_STATS_CACHE, _CLEAN_ITEMS_CACHE, _BUNDLES_CACHE, _REVIEW_TRENDS_CACHE
    _DATASET_STATS_CACHE = None
    _CLEAN_ITEMS_CACHE = None
    _BUNDLES_CACHE = None
    _REVIEW_TRENDS_CACHE = {}


def _trend_period(posted: datetime, granularity: str) -> tuple[str, str]:
    if granularity == "year":
        key = posted.strftime("%Y")
        return key, key
    if granularity == "week":
        iso = posted.isocalendar()
        key = f"{iso.year}-W{iso.week:02d}"
        week_start = datetime.fromisocalendar(iso.year, iso.week, 1).replace(tzinfo=timezone.utc)
        week_end = week_start + timedelta(days=6)
        label = f"{week_start.strftime('%d %b')} – {week_end.strftime('%d %b %Y')}"
        return key, label
    key = posted.strftime("%Y-%m")
    label = datetime(posted.year, posted.month, 1, tzinfo=timezone.utc).strftime("%b %Y")
    return key, label


def _effective_posted_at(item: dict[str, Any]) -> datetime | None:
    """Prefer review post date; fall back to cleaned_at for items missing posted_at."""
    posted_raw = item.get("posted_at") or item.get("cleaned_at")
    if not posted_raw:
        return None
    posted = datetime.fromisoformat(str(posted_raw).replace("Z", "+00:00"))
    if posted.tzinfo is None:
        posted = posted.replace(tzinfo=timezone.utc)
    return posted


def _period_keys_between(start: datetime, end: datetime, granularity: str) -> list[tuple[str, str]]:
    """All period keys from start through end (inclusive), in chronological order."""
    if granularity == "week":
        start_iso = start.isocalendar()
        cursor = datetime.fromisocalendar(start_iso.year, start_iso.week, 1).replace(tzinfo=timezone.utc)
        end_iso = end.isocalendar()
        end_key = f"{end_iso.year}-W{end_iso.week:02d}"
        keys: list[tuple[str, str]] = []
        seen: set[str] = set()
        while True:
            key, label = _trend_period(cursor, granularity)
            if key not in seen:
                keys.append((key, label))
                seen.add(key)
            if key == end_key:
                break
            cursor += timedelta(days=7)
        return keys

    if granularity == "month":
        cursor = datetime(start.year, start.month, 1, tzinfo=timezone.utc)
        end_key = end.strftime("%Y-%m")
        keys = []
        seen = set()
        while True:
            key, label = _trend_period(cursor, granularity)
            if key not in seen:
                keys.append((key, label))
                seen.add(key)
            if key == end_key:
                break
            if cursor.month == 12:
                cursor = datetime(cursor.year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                cursor = datetime(cursor.year, cursor.month + 1, 1, tzinfo=timezone.utc)
        return keys

    start_year = start.year
    end_year = end.year
    return [(str(y), str(y)) for y in range(start_year, end_year + 1)]


def _empty_trend_bucket(label: str = "") -> dict[str, Any]:
    return {
        "review_count": 0,
        "ratings": [],
        "positive": 0,
        "neutral": 0,
        "negative": 0,
        "label": label,
    }


def _chart_period_floor(granularity: str) -> str:
    key, _ = _trend_period(TRENDS_CHART_START, granularity)
    return key


class InsightsDatabase:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: Client = create_client(settings.supabase_url, settings.supabase_anon_key)
        self._insights = self._client.schema("insights")
        self._clean = self._client.schema("clean")

    def list_runs(self, *, limit: int = 50) -> list[dict[str, Any]]:
        response = (
            self._insights.table("synthesis_runs")
            .select("*")
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        response = (
            self._insights.table("synthesis_runs")
            .select("*")
            .eq("id", run_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def get_running_run(self) -> dict[str, Any] | None:
        response = (
            self._insights.table("synthesis_runs")
            .select("*")
            .eq("status", "running")
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def get_latest_successful_run(self) -> dict[str, Any] | None:
        response = (
            self._insights.table("synthesis_runs")
            .select("*")
            .eq("status", "success")
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if rows:
            return rows[0]

        response = (
            self._insights.table("synthesis_runs")
            .select("*")
            .gte("questions_answered", 6)
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def get_run_bundle(self, run_id: str) -> dict[str, Any] | None:
        run = self.get_run(run_id)
        if not run:
            return None

        answers = (
            self._insights.table("question_answers")
            .select("*")
            .eq("run_id", run_id)
            .execute()
            .data
            or []
        )
        summary_rows = (
            self._insights.table("executive_summary")
            .select("*")
            .eq("run_id", run_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        for answer in answers:
            stats = answer.get("stats") or {}
            if not answer.get("top_themes") and stats.get("top_themes"):
                answer["top_themes"] = stats["top_themes"]

        self._refresh_evidence_quotes(answers)

        bundle = {
            "run": run,
            "question_answers": answers,
            "executive_summary": summary_rows[0] if summary_rows else None,
            "dataset_stats": self.get_dataset_stats(),
        }
        bundle["run"]["questions_answered"] = len(answers)
        return bundle

    def get_latest_bundle(self) -> dict[str, Any] | None:
        run = self.get_latest_successful_run()
        if not run:
            return None
        return self.get_run_bundle(run["id"])

    def get_dataset_stats(self) -> dict[str, Any]:
        global _DATASET_STATS_CACHE
        now = time.time()
        if _DATASET_STATS_CACHE and now - _DATASET_STATS_CACHE[0] < _DATASET_STATS_TTL_SECONDS:
            return _DATASET_STATS_CACHE[1]

        ratings: list[int] = []
        rating_distribution: dict[str, int] = defaultdict(int)
        by_source: dict[str, int] = defaultdict(int)
        store_ratings: list[int] = []
        discovery_items: dict[str, dict[str, Any]] = {}

        phase3_src = str(self._settings.phase3_src)
        if phase3_src not in sys.path:
            sys.path.insert(0, phase3_src)
        try:
            from phase3_insights.aggregation import assign_questions
        except ImportError:
            assign_questions = None  # type: ignore[assignment,misc]

        items = self._fetch_all_clean_items()
        for item in items:
            source = item.get("source") or "unknown"
            by_source[source] += 1
            rating = item.get("rating")
            if rating is not None:
                star = int(rating)
                ratings.append(star)
                rating_distribution[str(star)] += 1
                if source in ("app_store", "google_play"):
                    store_ratings.append(star)
            else:
                rating_distribution["unknown"] += 1

            if assign_questions is not None and assign_questions(item):
                item_key = str(item.get("id") or item.get("source_item_id") or id(item))
                discovery_items[item_key] = item

        discovery_ratings = [
            int(item["rating"])
            for item in discovery_items.values()
            if item.get("rating") is not None
        ]

        stats = {
            "total_reviews": len(items),
            "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
            "rated_review_count": len(ratings),
            "discovery_review_count": len(discovery_items),
            "discovery_avg_rating": (
                round(sum(discovery_ratings) / len(discovery_ratings), 2)
                if discovery_ratings
                else None
            ),
            "discovery_rated_count": len(discovery_ratings),
            "store_avg_rating": (
                round(sum(store_ratings) / len(store_ratings), 2) if store_ratings else None
            ),
            "store_rated_count": len(store_ratings),
            "rating_distribution": dict(rating_distribution),
            "by_source": dict(by_source),
        }
        _DATASET_STATS_CACHE = (now, stats)
        return stats

    def _fetch_all_clean_items(self) -> list[dict[str, Any]]:
        global _CLEAN_ITEMS_CACHE
        now = time.time()
        if _CLEAN_ITEMS_CACHE and now - _CLEAN_ITEMS_CACHE[0] < _DATASET_STATS_TTL_SECONDS:
            return _CLEAN_ITEMS_CACHE[1]

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

        _CLEAN_ITEMS_CACHE = (now, items)
        return items

    def _get_bundles(self) -> dict[str, Any]:
        global _BUNDLES_CACHE
        now = time.time()
        if _BUNDLES_CACHE and now - _BUNDLES_CACHE[0] < _DATASET_STATS_TTL_SECONDS:
            return _BUNDLES_CACHE[1]

        phase3_src = str(self._settings.phase3_src)
        if phase3_src not in sys.path:
            sys.path.insert(0, phase3_src)

        try:
            from phase3_insights.aggregation import build_bundles
        except ImportError:
            return {}

        bundles = build_bundles(self._fetch_all_clean_items())
        _BUNDLES_CACHE = (now, bundles)
        return bundles

    def _refresh_evidence_quotes(self, answers: list[dict[str, Any]]) -> None:
        """Re-select evidence quotes from clean items using fixed aggregation logic."""
        bundles = self._get_bundles()
        if not bundles:
            return

        by_question = {a["question_id"]: a for a in answers}
        for qid, bundle in bundles.items():
            answer = by_question.get(qid)
            if not answer:
                continue
            answer["evidence_quotes"] = [q.to_dict() for q in bundle.quotes]
            answer["stats"] = bundle.stats.to_dict()

    def get_trends(self, granularity: str = "month") -> dict[str, Any]:
        """Review sentiment and rating trends bucketed by week, month, or year."""
        if granularity not in TREND_GRANULARITIES:
            granularity = "month"

        global _REVIEW_TRENDS_CACHE
        cache_ts = time.time()
        cached = _REVIEW_TRENDS_CACHE.get(granularity)
        if cached and cache_ts - cached[0] < _DATASET_STATS_TTL_SECONDS:
            return cached[1]

        buckets: dict[str, dict[str, Any]] = defaultdict(_empty_trend_bucket)
        range_start: datetime | None = None
        range_end: datetime | None = None
        skipped_no_date = 0
        as_of = datetime.now(timezone.utc)
        chart_floor = _chart_period_floor(granularity)

        for item in self._fetch_all_clean_items():
            posted = _effective_posted_at(item)
            if not posted:
                skipped_no_date += 1
                continue

            if posted < TRENDS_CHART_START:
                continue

            range_start = posted if range_start is None else min(range_start, posted)
            range_end = posted if range_end is None else max(range_end, posted)

            period_key, label = _trend_period(posted, granularity)
            bucket = buckets[period_key]
            if not bucket["label"]:
                bucket["label"] = label
            bucket["review_count"] += 1

            rating = item.get("rating")
            if rating is None:
                continue

            star = int(rating)
            bucket["ratings"].append(star)
            if star >= 4:
                bucket["positive"] += 1
            elif star == 3:
                bucket["neutral"] += 1
            else:
                bucket["negative"] += 1

        # Pad from January 2026 through the current period.
        for period_key, label in _period_keys_between(TRENDS_CHART_START, as_of, granularity):
            if period_key not in buckets:
                buckets[period_key] = _empty_trend_bucket(label)
            elif not buckets[period_key]["label"]:
                buckets[period_key]["label"] = label

        periods: list[dict[str, Any]] = []
        for period_key in sorted(buckets.keys()):
            if period_key < chart_floor:
                continue
            bucket = buckets[period_key]
            ratings: list[int] = bucket["ratings"]
            rated_count = len(ratings)
            avg_rating = round(sum(ratings) / rated_count, 2) if rated_count else None
            if rated_count:
                sentiment_score = round(
                    (bucket["positive"] - bucket["negative"]) / rated_count * 100,
                    1,
                )
                positive_pct = round(bucket["positive"] / rated_count * 100, 1)
                neutral_pct = round(bucket["neutral"] / rated_count * 100, 1)
                negative_pct = round(bucket["negative"] / rated_count * 100, 1)
            else:
                sentiment_score = None
                positive_pct = neutral_pct = negative_pct = 0.0

            periods.append(
                {
                    "period": period_key,
                    "label": bucket["label"],
                    "review_count": bucket["review_count"],
                    "rated_count": rated_count,
                    "avg_rating": avg_rating,
                    "sentiment_score": sentiment_score,
                    "positive_pct": positive_pct,
                    "neutral_pct": neutral_pct,
                    "negative_pct": negative_pct,
                }
            )

        result = {
            "granularity": granularity,
            "range_start": TRENDS_CHART_START.isoformat(),
            "range_end": as_of.isoformat(),
            "data_through": (range_end.isoformat() if range_end else None),
            "total_reviews": sum(p["review_count"] for p in periods),
            "skipped_no_date": skipped_no_date,
            "periods": periods,
        }
        _REVIEW_TRENDS_CACHE[granularity] = (cache_ts, result)
        return result
