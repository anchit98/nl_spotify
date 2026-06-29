from __future__ import annotations

from datetime import datetime
from enum import Enum

from phase1_collection.config import Settings, initial_window_start, utc_now
from phase1_collection.db import Database


class CollectionMode(str, Enum):
    PROBE = "probe"
    INITIAL = "initial"
    WEEKLY = "weekly"
    ADHOC = "adhoc"


def parse_mode(value: str) -> CollectionMode:
    try:
        return CollectionMode(value.lower())
    except ValueError as exc:
        valid = ", ".join(m.value for m in CollectionMode)
        raise ValueError(f"Invalid collection mode '{value}'. Choose one of: {valid}") from exc


def window_start_for_mode(
    mode: CollectionMode,
    settings: Settings,
    db: Database,
    source: str,
) -> datetime:
    from datetime import timedelta

    initial_start = initial_window_start(settings)

    if mode == CollectionMode.INITIAL:
        return initial_start
    if mode == CollectionMode.ADHOC:
        return utc_now() - timedelta(days=settings.adhoc_lookback_days)
    if mode == CollectionMode.PROBE:
        return initial_start
    return db.get_window_start(source, initial_start)
