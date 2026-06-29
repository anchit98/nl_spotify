"""Research questions and mapping from Phase 2 topic tags."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

RESEARCH_QUESTIONS: dict[str, str] = {
    "q1_discovery_barriers": "Why do users struggle to discover new music?",
    "q2_recommendation_frustrations": "What are the most common frustrations with recommendations?",
    "q3_listening_goals": "What listening behaviors are users trying to achieve?",
    "q4_repetitive_listening": "What causes users to repeatedly listen to the same content?",
    "q5_segment_differences": "Which user segments experience different discovery challenges?",
    "q6_unmet_needs": "What unmet needs emerge consistently across reviews?",
}

# Phase 2 clean.feedback_items.topics_matched values -> question ids
TOPIC_TO_QUESTION: dict[str, str] = {
    "struggle_discovery": "q1_discovery_barriers",
    "recommendation_frustrations": "q2_recommendation_frustrations",
    "listening_behaviors": "q3_listening_goals",
    "repeated_listening": "q4_repetitive_listening",
    "user_segments": "q5_segment_differences",
    "unmet_needs": "q6_unmet_needs",
}

PAIN_QUESTIONS = frozenset({
    "q1_discovery_barriers",
    "q2_recommendation_frustrations",
    "q4_repetitive_listening",
})


@dataclass
class EvidenceQuote:
    text: str
    source: str
    rating: int | None
    posted_at: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "source": self.source,
            "rating": self.rating,
            "posted_at": self.posted_at,
        }


@dataclass
class QuestionStats:
    total_mentions: int = 0
    by_source: dict[str, int] = field(default_factory=dict)
    rating_distribution: dict[str, int] = field(default_factory=dict)
    avg_rating: float | None = None
    low_rating_count: int = 0  # rating <= 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_mentions": self.total_mentions,
            "by_source": self.by_source,
            "rating_distribution": self.rating_distribution,
            "avg_rating": self.avg_rating,
            "low_rating_count": self.low_rating_count,
        }


@dataclass
class QuestionBundle:
    question_id: str
    question_text: str
    stats: QuestionStats
    quotes: list[EvidenceQuote] = field(default_factory=list)
    theme_counts: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "stats": self.stats.to_dict(),
            "quotes": [q.to_dict() for q in self.quotes],
            "computed_themes": [
                t.to_dict() if hasattr(t, "to_dict") else t for t in self.theme_counts
            ],
        }
