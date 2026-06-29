from __future__ import annotations

import httpx

from phase5_ops.config import Settings
from phase5_ops.db import Database
from phase5_ops.drift_detector import AlertCandidate


def _format_slack_payload(alert: AlertCandidate) -> dict[str, Any]:
    emoji = {"info": ":information_source:", "warning": ":warning:", "critical": ":rotating_light:"}.get(
        alert.severity, ":bell:"
    )
    return {
        "text": f"{emoji} *[{alert.severity.upper()}] {alert.title}*\n{alert.message}",
    }


def send_webhook(settings: Settings, alert: AlertCandidate) -> bool:
    if not settings.alert_webhook_url:
        return False
    payload = _format_slack_payload(alert)
    try:
        response = httpx.post(
            settings.alert_webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15.0,
        )
        response.raise_for_status()
        return True
    except httpx.HTTPError as exc:
        print(f"Webhook delivery failed: {exc}", flush=True)
        return False


def persist_and_notify(
    db: Database,
    settings: Settings,
    candidates: list[AlertCandidate],
    *,
    dedupe_hours: int = 24,
) -> list[UUID]:
    """Store alerts and optionally notify via webhook. Dedupes by category+title."""
    fired: list[UUID] = []
    for alert in candidates:
        if db.recent_alert_exists(alert.category, alert.title, hours=dedupe_hours):
            print(f"SKIP (deduped): {alert.title}")
            continue
        row = {
            "severity": alert.severity,
            "category": alert.category,
            "title": alert.title,
            "message": alert.message,
            "context": alert.context,
            "notified": False,
        }
        alert_id = db.save_alert(row)
        fired.append(alert_id)
        if send_webhook(settings, alert):
            db.mark_alert_notified(alert_id)
        print(f"ALERT [{alert.severity}] {alert.title}: {alert.message}")
    return fired


def pipeline_failure_alert(workflow: str, job: str, error_summary: str) -> AlertCandidate:
    return AlertCandidate(
        severity="critical",
        category="pipeline_failure",
        title=f"GitHub Actions pipeline failed: {job}",
        message=(
            f"Workflow `{workflow}` job `{job}` failed.\n{error_summary}\n"
            "Check Actions logs and re-run after fixing."
        ),
        context={"workflow": workflow, "job": job},
    )
