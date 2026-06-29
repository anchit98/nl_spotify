from __future__ import annotations

from typing import Any

from phase5_ops.db import Database


def _themes_from_answer(answer: dict[str, Any]) -> list[dict[str, Any]]:
    top = answer.get("top_themes")
    if isinstance(top, list) and top:
        return top
    stats = answer.get("stats") or {}
    nested = stats.get("top_themes")
    if isinstance(nested, list):
        return nested
    return []


def extract_theme_trends(db: Database, run_id: str) -> list[dict[str, Any]]:
    """Persist theme mention counts for one synthesis run."""
    answers = db.fetch_question_answers(run_id)
    rows: list[dict[str, Any]] = []
    for answer in answers:
        qid = answer.get("question_id")
        if not qid:
            continue
        for theme_row in _themes_from_answer(answer):
            theme = (theme_row.get("theme") or "").strip()
            if not theme:
                continue
            rows.append(
                {
                    "synthesis_run_id": run_id,
                    "question_id": qid,
                    "theme": theme,
                    "mention_count": int(theme_row.get("mention_count") or 0),
                }
            )
    db.upsert_theme_trends(rows)
    return rows


def find_sustained_theme_spikes(
    db: Database,
    *,
    spike_pct: float,
    min_mentions: int,
) -> list[dict[str, Any]]:
    """
    Compare the two most recent successful synthesis runs.
    Flag themes that rose >= spike_pct in BOTH step (current vs previous).
    """
    runs = [r for r in db.fetch_recent_synthesis_runs(limit=10) if r.get("status") == "success"]
    if len(runs) < 2:
        return []

    current_id = runs[0]["id"]
    previous_id = runs[1]["id"]
    current = {
        (r["question_id"], r["theme"]): int(r["mention_count"] or 0)
        for r in db.fetch_theme_trends_for_run(current_id)
    }
    previous = {
        (r["question_id"], r["theme"]): int(r["mention_count"] or 0)
        for r in db.fetch_theme_trends_for_run(previous_id)
    }

    if not current:
        extract_theme_trends(db, current_id)
        extract_theme_trends(db, previous_id)
        current = {
            (r["question_id"], r["theme"]): int(r["mention_count"] or 0)
            for r in db.fetch_theme_trends_for_run(current_id)
        }
        previous = {
            (r["question_id"], r["theme"]): int(r["mention_count"] or 0)
            for r in db.fetch_theme_trends_for_run(previous_id)
        }

    spikes: list[dict[str, Any]] = []
    for key, cur_count in current.items():
        if cur_count < min_mentions:
            continue
        prev_count = previous.get(key, 0)
        if prev_count <= 0:
            continue
        pct_change = (cur_count - prev_count) / prev_count * 100
        if pct_change >= spike_pct:
            qid, theme = key
            spikes.append(
                {
                    "question_id": qid,
                    "theme": theme,
                    "previous_count": prev_count,
                    "current_count": cur_count,
                    "pct_change": round(pct_change, 1),
                    "current_run_id": current_id,
                    "previous_run_id": previous_id,
                }
            )
    spikes.sort(key=lambda s: s["pct_change"], reverse=True)
    return spikes
