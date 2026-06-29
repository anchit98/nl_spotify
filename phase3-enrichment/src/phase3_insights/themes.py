"""Sub-theme keyword groups per research question for deterministic counting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

THEME_DEFINITIONS: dict[str, dict[str, list[str]]] = {
    "q1_discovery_barriers": {
        "hard_to_find": ["hard to find", "can't find", "cannot find", "difficult to find", "struggle to find"],
        "search_problems": ["search", "looking for", "find music", "find songs"],
        "explore_limits": ["explore", "unfamiliar", "new music", "discover"],
        "catalog_gaps": ["not on spotify", "missing artist", "missing song", "not available"],
        "discovery_praise": ["easy to discover", "great discovery", "love discovering", "find new artists"],
    },
    "q2_recommendation_frustrations": {
        "algorithm_complaints": ["algorithm", "bad recommend", "terrible recommend", "awful suggest", "sucks"],
        "wrong_music": ["wrong genre", "don't like", "not what i like", "irrelevant", "don't listen to"],
        "discover_weekly": ["discover weekly", "daily mix", "release radar", "made for you"],
        "repetitive_recs": ["same songs", "repetitive", "again and again", "always the same"],
        "poor_quality": ["bad quality", "terrible", "awful", "worst", "garbage"],
    },
    "q3_listening_goals": {
        "relaxation": ["relax", "relaxing", "calm", "chill", "unwind", "sleep"],
        "workout": ["workout", "gym", "exercise", "running", "train"],
        "focus_study": ["focus", "study", "work", "concentrate", "background"],
        "mood_vibe": ["mood", "vibe", "feeling", "atmosphere"],
        "party_social": ["party", "dance", "friends", "social", "gathering"],
    },
    "q4_repetitive_listening": {
        "same_songs": ["same songs", "same song", "same music", "same track"],
        "same_artists": ["same artists", "same artist", "same band"],
        "repeat_loop": ["repeat", "loop", "over and over", "again and again"],
        "tired_bored": ["tired of", "bored", "sick of", "had enough"],
        "playlist_stuck": ["playlist", "keep playing", "always play"],
    },
    "q5_segment_differences": {
        "ads_frustration": ["too many ads", "ads are", "ad every", "hate ads", "stop ads"],
        "premium_value": ["premium", "subscription", "paying", "worth it", "upgrade"],
        "free_tier": ["free version", "free user", "free tier", "without premium"],
        "family_kids": ["family plan", "kids", "children", "child"],
        "student": ["student", "student discount", "university"],
    },
    "q6_unmet_needs": {
        "feature_requests": ["please add", "feature request", "bring back", "would be nice", "should have"],
        "missing_songs": ["more songs", "more music", "missing", "want more", "need more"],
        "playback_controls": ["skip", "stop", "shuffle", "pause", "control"],
        "ui_usability": ["interface", "layout", "hard to use", "confusing", "navigate"],
        "offline_download": ["offline", "download", "without internet"],
    },
}

THEME_LABELS: dict[str, str] = {
    "hard_to_find": (
        "Users say they cannot find music that fits their taste, even when they try to look for something new."
    ),
    "search_problems": (
        "People run into problems using search — results fail, songs show as unavailable, or lookups do not work as expected."
    ),
    "explore_limits": (
        "Users talk about exploring or discovering new music, but often in the context of difficulty or mixed results."
    ),
    "catalog_gaps": (
        "Reviews mention artists, albums, or songs that seem to be missing or hard to access on the platform."
    ),
    "discovery_praise": (
        "Some users describe discovering new music as easy and enjoyable, which shows discovery works well for part of the audience."
    ),
    "algorithm_complaints": (
        "Users blame the recommendation algorithm for suggesting music that feels wrong, repetitive, or out of touch with their taste."
    ),
    "wrong_music": (
        "People receive suggestions for genres or songs they clearly do not like and feel the app does not understand what they listen to."
    ),
    "discover_weekly": (
        "Users refer to curated playlists like Discover Weekly, Daily Mix, or Release Radar when talking about recommendations."
    ),
    "repetitive_recs": (
        "Listeners complain that recommendations and mixes keep serving the same songs instead of surfacing fresh music."
    ),
    "poor_quality": (
        "Reviews use strong negative language about the overall quality of suggestions, ads, or the listening experience tied to recommendations."
    ),
    "relaxation": (
        "People use Spotify to unwind — they want calm, relaxing, or sleep-friendly music in the background."
    ),
    "workout": (
        "Users listen while exercising and look for upbeat or motivating music for workouts and the gym."
    ),
    "focus_study": (
        "Listeners use music to concentrate while studying, working, or doing tasks in the background."
    ),
    "mood_vibe": (
        "Users care about setting a mood or vibe — they want playlists that match how they feel or the atmosphere they want."
    ),
    "party_social": (
        "People listen in social settings and want music for parties, dancing, or sharing with friends."
    ),
    "same_songs": (
        "Users notice the same individual songs coming back again and again, even in large playlists."
    ),
    "same_artists": (
        "Listeners feel stuck hearing the same artists repeatedly instead of a wider variety."
    ),
    "repeat_loop": (
        "People want to repeat or loop tracks — or complain that repeat and shuffle behaviour does not work as they expect."
    ),
    "tired_bored": (
        "Users say they are bored or tired of hearing the same content and want more variety."
    ),
    "playlist_stuck": (
        "Listeners feel their playlists or the app keep playing the same rotation of songs without real variety."
    ),
    "ads_frustration": (
        "Free-tier users are frustrated by how often ads interrupt their music and how intrusive the ad experience feels."
    ),
    "premium_value": (
        "Users debate whether paying for Premium is worth it — some praise ad-free listening, others feel features do not justify the cost."
    ),
    "free_tier": (
        "People on the free plan describe limits like ads, shuffle-only playback, or not being able to pick songs in order."
    ),
    "family_kids": (
        "Reviews mention family plans, kids, or child-friendly content when talking about who uses the app and how."
    ),
    "student": (
        "Students comment on pricing, discounts, or whether the app is affordable on a student budget."
    ),
    "feature_requests": (
        "Users ask for specific features to be added, brought back, or improved rather than just complaining in general."
    ),
    "missing_songs": (
        "People want a bigger music library and say certain songs, genres, or artists they care about are missing."
    ),
    "playback_controls": (
        "Listeners want better control over playback — skipping, stopping, shuffling, or how songs play in playlists."
    ),
    "ui_usability": (
        "Users find parts of the app confusing or harder to use, especially around layout, navigation, or recent design changes."
    ),
    "offline_download": (
        "People want to download music or listen offline without needing an internet connection."
    ),
}

MAX_THEMES_PER_QUESTION = 5
MAX_SAMPLE_QUOTES_PER_THEME = 2


@dataclass
class ThemeCount:
    theme_id: str
    label: str
    mention_count: int
    sample_quotes: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "theme_id": self.theme_id,
            "label": self.label,
            "mention_count": self.mention_count,
            "sample_quotes": self.sample_quotes,
        }


def _matches_theme(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def compute_theme_counts(
    items: list[dict[str, Any]],
    question_id: str,
    *,
    pain_question: bool,
) -> list[ThemeCount]:
    definitions = THEME_DEFINITIONS.get(question_id, {})
    if not definitions:
        return []

    counts: dict[str, int] = {theme_id: 0 for theme_id in definitions}
    samples: dict[str, list[dict[str, Any]]] = {theme_id: [] for theme_id in definitions}

    for item in items:
        text = (item.get("cleaned_text") or "").strip()
        if not text:
            continue
        for theme_id, keywords in definitions.items():
            if not _matches_theme(text, keywords):
                continue
            counts[theme_id] += 1
            if len(samples[theme_id]) < MAX_SAMPLE_QUOTES_PER_THEME:
                samples[theme_id].append(
                    {
                        "text": text[:300],
                        "source": item.get("source") or "unknown",
                        "rating": item.get("rating"),
                    }
                )

    ranked = sorted(counts.items(), key=lambda pair: pair[1], reverse=True)
    themes: list[ThemeCount] = []
    for theme_id, mention_count in ranked:
        if mention_count == 0:
            continue
        themes.append(
            ThemeCount(
                theme_id=theme_id,
                label=THEME_LABELS.get(theme_id, theme_id.replace("_", " ").title()),
                mention_count=mention_count,
                sample_quotes=samples[theme_id],
            )
        )
        if len(themes) >= MAX_THEMES_PER_QUESTION:
            break

    if pain_question:
        themes.sort(key=lambda t: t.mention_count, reverse=True)

    return themes
