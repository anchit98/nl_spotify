from __future__ import annotations

import argparse
import sys

from phase5_ops.alerter import persist_and_notify, pipeline_failure_alert
from phase5_ops.config import Settings
from phase5_ops.db import Database
from phase5_ops.drift_detector import AlertCandidate, detect_drift
from phase5_ops.health_collector import collect_health_snapshot
from phase5_ops.model_registry import load_thresholds, sync_model_registry
from phase5_ops.preflight import run_preflight
from phase5_ops.report import write_health_report
from phase5_ops.theme_tracker import extract_theme_trends, find_sustained_theme_spikes


def run_monitor(*, trigger: str = "manual") -> int:
    settings = Settings.from_env()
    run_preflight(settings)
    db = Database(settings)
    thresholds = load_thresholds(settings.phase5_root)

    print(f"Phase 5 monitor — trigger={trigger}", flush=True)

    snapshot = collect_health_snapshot(db, trigger=trigger)
    snapshot_id = db.save_health_snapshot(snapshot)
    print(f"Health snapshot saved: {snapshot_id}", flush=True)

    run_id = snapshot.get("latest_synthesis_run_id")
    if run_id and snapshot.get("synthesis_status") == "success":
        themes = extract_theme_trends(db, str(run_id))
        print(f"Theme trends recorded: {len(themes)} rows for run {run_id}", flush=True)

    candidates = detect_drift(db, snapshot, thresholds)
    candidates.extend(
        sync_model_registry(
            db,
            settings,
            latest_synthesis_model=snapshot.get("synthesis_model"),
            thresholds=thresholds,
        )
    )

    if thresholds.get("alert_on_missing_executive_summary") and run_id:
        if snapshot.get("synthesis_status") == "success" and not db.has_executive_summary(str(run_id)):
            candidates.append(
                AlertCandidate(
                    severity="warning",
                    category="synthesis_quality",
                    title="Executive summary missing on latest run",
                    message=(
                        "Latest successful synthesis has no executive summary — often caused by "
                        "Groq daily token limits. Dashboard home may look incomplete."
                    ),
                    context={"run_id": run_id},
                )
            )

    spikes = find_sustained_theme_spikes(
        db,
        spike_pct=float(thresholds.get("theme_spike_pct", 75)),
        min_mentions=int(thresholds.get("theme_spike_min_mentions", 10)),
    )
    for spike in spikes[:5]:
        candidates.append(
            AlertCandidate(
                severity="info",
                category="theme_spike",
                title=f"Rising theme: {spike['theme']}",
                message=(
                    f"Question {spike['question_id']}: '{spike['theme']}' rose "
                    f"{spike['previous_count']} → {spike['current_count']} "
                    f"(+{spike['pct_change']}%) across the last two synthesis runs."
                ),
                context=spike,
            )
        )

    fired = persist_and_notify(db, settings, candidates)
    report_path = write_health_report(
        db,
        snapshot,
        len(fired),
        spikes,
        output_dir=settings.phase5_root / "reports",
    )
    print(f"Report written: {report_path}", flush=True)

    if any(c.severity == "critical" for c in candidates):
        return 1
    return 0


def run_pipeline_alert(workflow: str, job: str, error_summary: str) -> int:
    settings = Settings.from_env()
    db = Database(settings)
    alert = pipeline_failure_alert(workflow, job, error_summary)
    persist_and_notify(db, settings, [alert], dedupe_hours=6)
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 5: Operations monitoring and alerts")
    sub = parser.add_subparsers(dest="command", required=True)

    mon = sub.add_parser("monitor", help="Capture health snapshot, detect drift, alert")
    mon.add_argument(
        "--trigger",
        default="manual",
        choices=["manual", "weekly", "post_pipeline", "adhoc"],
        help="What triggered this monitor run",
    )

    fail = sub.add_parser("pipeline-failure", help="Fire alert for a failed GitHub Actions job")
    fail.add_argument("--workflow", required=True)
    fail.add_argument("--job", required=True)
    fail.add_argument("--error", default="See GitHub Actions logs for details.")

    args = parser.parse_args()
    if args.command == "monitor":
        code = run_monitor(trigger=args.trigger)
    else:
        code = run_pipeline_alert(args.workflow, args.job, args.error)
    sys.exit(code)


if __name__ == "__main__":
    main()
