from __future__ import annotations

from collections import defaultdict
from typing import Any

from phase3_insights.questions import (
    PAIN_QUESTIONS,
    EvidenceQuote,
    QuestionBundle,
    QuestionStats,
    RESEARCH_QUESTIONS,
    TOPIC_TO_QUESTION,
)
from phase3_insights.themes import compute_theme_counts

MAX_QUOTES_PER_QUESTION = 30
PAGE_SIZE = 1000


def _rating_bucket(rating: int | None) -> str:
    if rating is None:
        return "unknown"
    return str(rating)


def _quote_score(item: dict[str, Any], question_id: str) -> tuple[int, int, int]:
    """Sort key: prefer lower ratings to surface critical feedback, then longer text."""
    _ = question_id
    rating = item.get("rating")
    text_len = len(item.get("cleaned_text") or "")
    rating_sort = int(rating) if rating is not None else 99
    return (rating_sort, -text_len, 0 if rating is None else 1)


def _select_balanced_quotes(
    items: list[dict[str, Any]],
    question_id: str,
    *,
    max_quotes: int = MAX_QUOTES_PER_QUESTION,
) -> list[EvidenceQuote]:
    """Pick quotes in round-robin across sources so no single source dominates."""
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        text = (item.get("cleaned_text") or "").strip()
        if text:
            by_source[item.get("source") or "unknown"].append(item)

    queues: dict[str, list[dict[str, Any]]] = {}
    for source, source_items in by_source.items():
        queues[source] = sorted(source_items, key=lambda i: _quote_score(i, question_id))

    quotes: list[EvidenceQuote] = []
    seen_text: set[str] = set()
    active = sorted(queues.keys())

    while len(quotes) < max_quotes and active:
        next_active: list[str] = []
        for source in active:
            if len(quotes) >= max_quotes:
                break
            queue = queues[source]
            while queue:
                item = queue.pop(0)
                text = (item.get("cleaned_text") or "").strip()
                if text in seen_text:
                    continue
                seen_text.add(text)
                quotes.append(
                    EvidenceQuote(
                        text=text[:500],
                        source=source,
                        rating=item.get("rating"),
                        posted_at=item.get("posted_at"),
                    )
                )
                break
            if queue:
                next_active.append(source)
        active = next_active

    return quotes


def assign_questions(item: dict[str, Any]) -> list[str]:
    topics = item.get("topics_matched") or []
    if isinstance(topics, str):
        topics = [topics]
    question_ids: list[str] = []
    for topic in topics:
        qid = TOPIC_TO_QUESTION.get(topic)
        if qid and qid not in question_ids:
            question_ids.append(qid)
    return question_ids


def build_bundles(clean_items: list[dict[str, Any]]) -> dict[str, QuestionBundle]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for item in clean_items:
        for qid in assign_questions(item):
            buckets[qid].append(item)

    bundles: dict[str, QuestionBundle] = {}
    for qid, question_text in RESEARCH_QUESTIONS.items():
        items = buckets.get(qid, [])
        stats = QuestionStats()
        stats.total_mentions = len(items)

        ratings: list[int] = []
        for item in items:
            source = item.get("source") or "unknown"
            stats.by_source[source] = stats.by_source.get(source, 0) + 1
            rating = item.get("rating")
            bucket = _rating_bucket(rating)
            stats.rating_distribution[bucket] = stats.rating_distribution.get(bucket, 0) + 1
            if rating is not None:
                ratings.append(int(rating))
                if int(rating) <= 3:
                    stats.low_rating_count += 1

        if ratings:
            stats.avg_rating = round(sum(ratings) / len(ratings), 2)

        quotes = _select_balanced_quotes(items, qid)

        bundles[qid] = QuestionBundle(
            question_id=qid,
            question_text=question_text,
            stats=stats,
            quotes=quotes,
            theme_counts=compute_theme_counts(
                items,
                qid,
                pain_question=qid in PAIN_QUESTIONS,
            ),
        )

    return bundles
