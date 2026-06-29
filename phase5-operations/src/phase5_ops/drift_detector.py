from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any

from phase5_ops.db import Database


@dataclass
class AlertCandidate:
    severity: str
    category: str
    title: str
    message: str
    context: dict[str, Any]


def _median(values: list[int | float]) -> float:
    if not values:
        return 0.0
    return float(statistics.median(values))


def detect_drift(
    db: Database,
    current: dict[str, Any],
    thresholds: dict[str, Any],
) -> list[AlertCandidate]:
    """Compare current snapshot to rolling baseline; emit alert candidates."""
    alerts: list[AlertCandidate] = []
    history = db.fetch_health_snapshots(limit=int(thresholds.get("min_snapshots_for_baseline", 3)) + 1)
    prior = history[1:] if history else []

    min_baseline = int(thresholds.get("min_snapshots_for_baseline", 3))
    if len(prior) < min_baseline:
        return alerts

    # Corpus shrink
    shrink_pct = float(thresholds.get("corpus_shrink_pct", 10))
    prior_totals = [int(h.get("corpus_clean_total") or 0) for h in prior]
    median_corpus = _median(prior_totals)
    current_corpus = int(current.get("corpus_clean_total") or 0)
    if median_corpus > 0 and current_corpus < median_corpus * (1 - shrink_pct / 100):
        drop = round((1 - current_corpus / median_corpus) * 100, 1)
        alerts.append(
            AlertCandidate(
                severity="warning",
                category="corpus_drift",
                title="Clean corpus shrank vs baseline",
                message=(
                    f"Clean items {current_corpus:,} vs median {median_corpus:,.0f} "
                    f"({drop}% drop). Investigate cleaning filters or source outages."
                ),
                context={"current": current_corpus, "median": median_corpus},
            )
        )

    # Per-source collection volume drop
    drop_pct = float(thresholds.get("collection_volume_drop_pct", 50))
    current_sources = current.get("collection_by_source") or {}
    for source, cur_data in current_sources.items():
        cur_items = int(cur_data.get("items_collected_7d") or 0)
        hist_items = []
        for h in prior:
            src = (h.get("collection_by_source") or {}).get(source) or {}
            hist_items.append(int(src.get("items_collected_7d") or 0))
        med = _median(hist_items)
        if med >= 5 and cur_items < med * (1 - drop_pct / 100):
            alerts.append(
                AlertCandidate(
                    severity="warning",
                    category="collection_drift",
                    title=f"Collection volume drop: {source}",
                    message=(
                        f"{source} collected {cur_items} items in 7d vs median {med:,.0f} "
                        f"(>{drop_pct}% drop). Check connector health."
                    ),
                    context={"source": source, "current": cur_items, "median": med},
                )
            )

    # Collection failures in window
    if int(current.get("collection_failures") or 0) > 0:
        alerts.append(
            AlertCandidate(
                severity="critical",
                category="collection_failure",
                title="Collection failures in last 7 days",
                message=(
                    f"{current['collection_failures']} failed collection run(s) in the past week. "
                    "See raw.collection_runs for details."
                ),
                context={"failures": current["collection_failures"]},
            )
        )

    # Synthesis failure
    if thresholds.get("alert_on_synthesis_failure", True):
        status = current.get("synthesis_status")
        if status and status != "success":
            alerts.append(
                AlertCandidate(
                    severity="critical",
                    category="synthesis_failure",
                    title="Latest synthesis run not successful",
                    message=f"Most recent synthesis status: {status}. Check insights.synthesis_runs.",
                    context={"status": status, "run_id": current.get("latest_synthesis_run_id")},
                )
            )

    return alerts
