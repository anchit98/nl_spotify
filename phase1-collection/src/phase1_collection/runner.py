from __future__ import annotations

import argparse
import sys
import traceback

from phase1_collection.collection_mode import CollectionMode, parse_mode, window_start_for_mode
from phase1_collection.config import Settings, utc_now
from phase1_collection.connectors import get_connector
from phase1_collection.db import Database
from phase1_collection.preflight import run_preflight

MODE_DESCRIPTIONS = {
    CollectionMode.PROBE: "small sample per source (connectivity check)",
    CollectionMode.INITIAL: (
        "one-time bootstrap — full lookback window, no pagination caps, ignores prior watermarks"
    ),
    CollectionMode.WEEKLY: "incremental — everything since the last successful run (append only)",
    CollectionMode.ADHOC: "manual refresh — last ADHOC_LOOKBACK_DAYS only (default 7), append only",
}


def run_collection(mode: CollectionMode = CollectionMode.WEEKLY) -> None:
    settings = Settings.from_env()
    sources = list(settings.enabled_sources)

    if not sources:
        print("No sources enabled. Exiting.")
        sys.exit(0)

    run_preflight(settings, sources)

    db = Database(settings)
    now = utc_now()
    failures = 0

    print(f"Collection mode: {mode.value} — {MODE_DESCRIPTIONS[mode]}")
    if mode == CollectionMode.INITIAL:
        print(
            f"Initial extract window: last {settings.initial_lookback_days} days, "
            "no artificial per-source limits."
        )
    elif mode == CollectionMode.ADHOC:
        print(f"Ad-hoc window: last {settings.adhoc_lookback_days} days.")

    for source in sources:
        print(f"--- Collecting {source} ---")
        connector = get_connector(source, settings)

        hc = connector.health_check()
        if not hc.ok:
            print(f"Health check failed for {source}: {hc.message}", file=sys.stderr)
            failures += 1
            continue

        window_start = window_start_for_mode(mode, settings, db, source)
        window_end = now
        print(f"Window: {window_start.isoformat()} to {window_end.isoformat()}")

        run_id = db.start_run(source, window_start, window_end)

        try:
            items = connector.collect(since=window_start, until=window_end, mode=mode)
            inserted = db.upsert_items(source, run_id, items)
            db.finish_run(
                run_id,
                "success",
                inserted,
                metadata={"mode": mode.value},
            )
            print(f"Success: collected {len(items)} items, inserted {inserted} new items.")
        except Exception as exc:  # noqa: BLE001
            err = traceback.format_exc()
            db.finish_run(run_id, "failed", 0, error_message=err, metadata={"mode": mode.value})
            print(f"Failed: {exc}", file=sys.stderr)
            failures += 1

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect public feedback into Supabase raw tables.")
    parser.add_argument(
        "--mode",
        choices=[m.value for m in CollectionMode],
        default=CollectionMode.WEEKLY.value,
        help="Collection mode (default: weekly)",
    )
    parser.add_argument(
        "--probe",
        action="store_true",
        help="Shortcut for --mode probe",
    )
    parser.add_argument(
        "--initial",
        action="store_true",
        help="Shortcut for --mode initial",
    )
    parser.add_argument(
        "--adhoc",
        action="store_true",
        help="Shortcut for --mode adhoc",
    )
    args = parser.parse_args()

    if sum([args.probe, args.initial, args.adhoc]) > 1:
        parser.error("Use only one of --probe, --initial, or --adhoc")

    if args.probe:
        mode = CollectionMode.PROBE
    elif args.initial:
        mode = CollectionMode.INITIAL
    elif args.adhoc:
        mode = CollectionMode.ADHOC
    else:
        mode = parse_mode(args.mode)

    run_collection(mode=mode)
